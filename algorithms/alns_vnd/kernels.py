"""Numba kernels of the ALNS + VND metaheuristic for static CVRPTW.

Everything performance-critical lives here: the solution data structure, O(1)
time-window feasibility tests, destroy/repair operators, the Variable
Neighbourhood Descent and the ALNS main loop.  The code is plain Python written
in the Numba-compatible subset (see ``_jit.py``).

Conventions
-----------
* Node 0 is the depot, customers are 1..n (the internal indices of
  ``CVRPTWInstance``).  ``N = n + 1``.
* A *route* is a doubly linked list of customers (``NXT``/``PRV``); the depot
  is represented by the sentinel value 0 at both ends.  At most ``R = min(K, n)``
  routes exist; an unused route has ``LEN == 0``.
* Time windows constrain the **start of service**.  Feasibility is evaluated
  with the time-window segment algebra of Vidal et al. (2013): a sequence of
  visits is summarised by (D, TW, E, L) = (minimum duration, time warp,
  earliest and latest start).  Concatenation is O(1) and a sequence is
  feasible iff its time warp is zero.  Every route keeps prefix segments
  (depot .. u) and suffix segments (u .. depot) at each node, so inserting,
  removing or exchanging customers/segments between routes is checked in O(1).
* Search states are always capacity- and time-window feasible.  Customers that
  cannot be inserted stay *unassigned* and are penalised in the objective; a
  state with unassigned customers is never reported as a solution.

Data passed to the kernels
--------------------------
Instance tuple ``inst = (dist, tt, ND, cap, nbrs, near, shaw, sym, empty_cost)``
where ``ND`` stacks per-node rows (TA, TB, SVC, DEM).
Solution tuple ``sol = (I, F, RI, RF, TST, SC, CTR)`` with the row layouts
below; ``CTR`` (a 1-element modification counter) is shared by all copies.

Performance note: handing these *tuples* to a non-inlined Numba function costs
~100 ns per call (reference counting of every member array), while handing
the arrays individually is essentially free.  Only the per-iteration entry
points therefore accept tuples; every function on a hot path takes arrays.
"""
import numpy as np

from ._jit import njit

# ---------------------------------------------------------------- layout --
# ND (float64, 4 x N): per-node instance data
TA = 0    # earliest service start
TB = 1    # latest service start
SVC = 2   # service duration
DEM = 3   # demand
# I  (int64,   4 x N): per-node links and positions
NXT = 0
PRV = 1
RTE = 2   # route id, -1 when unassigned
POS = 3   # 0-based position inside its route
# F  (float64, 10 x N): per-node segment data of its current route
PD = 0    # prefix segment depot..u : duration
PTW = 1   #                          time warp
PE = 2    #                          earliest start
PL = 3    #                          latest start
SD = 4    # suffix segment u..depot : duration
STW = 5
SE = 6
SL = 7
PLOAD = 8  # cumulative load depot..u
ES = 9     # earliest service start at u when leaving the depot at a0
# RI (int64,   4 x R): per-route integers
FIRST = 0
LAST = 1
LEN = 2
STAMP = 3  # value of CTR when the route last changed
# RF (float64, 2 x R): per-route floats
LOAD = 0
COST = 1
# SC (float64, 2): [routing distance, number of unassigned customers]

# VND neighbourhood identifiers (order configurable from Python)
NB_RELOCATE = 0
NB_SWAP = 1
NB_TWO_OPT_STAR = 2
NB_OR_OPT = 3
NB_TWO_OPT = 4
N_NEIGHBOURHOODS = 5

# destroy operators
D_RANDOM = 0
D_WORST = 1
D_SHAW = 2
D_STRING = 3
D_ROUTE = 4
N_DESTROY = 5
# repair operators
R_GREEDY = 0
R_REGRET2 = 1
R_REGRET3 = 2
R_BLINK = 3
N_REPAIR = 4

# integer parameter vector IP
IP_QMIN = 0
IP_QMAX = 1
IP_SEGMENT = 2
IP_RESTART = 3
IP_SISR_LMAX = 4
IP_ITER = 5            # global iteration counter (state)
IP_LAST_IMPROVE = 6    # iteration of the last best improvement (state)
IP_INSERT_ALL = 7      # 1: repair scans every route, 0: granular candidate routes
IP_VND_NEIGHBOURS = 8  # neighbours examined per customer in the VND
N_IP = 9
# float parameter vector P
P_WORST_P = 0
P_SHAW_P = 1
P_SISR_CBAR = 2
P_SISR_SPLIT = 3
P_SISR_BETA = 4
P_BLINK = 5
P_SIG1 = 6
P_SIG2 = 7
P_SIG3 = 8
P_REACTION = 9
P_PENALTY = 10
N_P = 11
# statistics vector ST (float64)
ST_ITERS = 0
ST_ACCEPT = 1
ST_IMPROVE_CUR = 2
ST_NEW_BEST = 3
ST_RESTARTS = 4
ST_INFEASIBLE_CAND = 5
ST_VND_MOVES = 6
N_ST = 7

EPS_TW = 1e-9     # time-warp tolerance (validator uses 1e-7, so we are stricter)
EPS_COST = 1e-7   # minimum strict improvement
EPS_LOAD = 1e-9
INF = 1e30
BIG_REGRET = 1e12


# ------------------------------------------------------- segment algebra --
@njit
def cat(D1, W1, E1, L1, D2, W2, E2, L2, t):
    """Concatenate two time-window segments separated by travel time t."""
    delta = D1 - W1 + t
    dwt = E2 - delta - L1
    if dwt < 0.0:
        dwt = 0.0
    dtw = E1 + delta - L2
    if dtw < 0.0:
        dtw = 0.0
    E = E2 - delta
    if E1 > E:
        E = E1
    L = L2 - delta
    if L1 < L:
        L = L1
    return D1 + D2 + t + dwt, W1 + W2 + dtw, E - dwt, L + dtw


@njit
def pre(F, ND, x):
    """Prefix segment depot..x (x == 0: the bare start depot)."""
    if x == 0:
        return 0.0, 0.0, ND[TA, 0], ND[TB, 0]
    return F[PD, x], F[PTW, x], F[PE, x], F[PL, x]


@njit
def suf(F, ND, x):
    """Suffix segment x..depot (x == 0: the bare end depot)."""
    if x == 0:
        return 0.0, 0.0, ND[TA, 0], ND[TB, 0]
    return F[SD, x], F[STW, x], F[SE, x], F[SL, x]


@njit
def pload(F, x):
    if x == 0:
        return 0.0
    return F[PLOAD, x]


@njit
def join_tw(tt, ND, F, p, x):
    """Time warp of prefix(p) + suffix(x): the route after deleting what lies between."""
    D1, W1, E1, L1 = pre(F, ND, p)
    D2, W2, E2, L2 = suf(F, ND, x)
    return cat(D1, W1, E1, L1, D2, W2, E2, L2, tt[p, x])[1]


@njit
def insert_tw(tt, ND, F, p, u, x):
    """Time warp of prefix(p) + u + suffix(x)."""
    D, W, E, L = pre(F, ND, p)
    D, W, E, L = cat(D, W, E, L, ND[SVC, u], 0.0, ND[TA, u], ND[TB, u], tt[p, u])
    D2, W2, E2, L2 = suf(F, ND, x)
    return cat(D, W, E, L, D2, W2, E2, L2, tt[u, x])[1]


@njit
def chain_seg(dist, tt, ND, I, first, length, reverse):
    """Segment of ``length`` consecutive nodes starting at ``first`` (following
    NXT), optionally visited in reverse order.  Returns (D, TW, E, L, cost)
    where cost is the internal travel distance in the visiting direction."""
    u = first
    if reverse:
        for k in range(length - 1):
            u = I[NXT, u]
    D, W, E, L = ND[SVC, u], 0.0, ND[TA, u], ND[TB, u]
    cost = 0.0
    for k in range(length - 1):
        v = I[PRV, u] if reverse else I[NXT, u]
        D, W, E, L = cat(D, W, E, L, ND[SVC, v], 0.0, ND[TA, v], ND[TB, v], tt[u, v])
        cost += dist[u, v]
        u = v
    return D, W, E, L, cost


# ------------------------------------------------------ route maintenance --
@njit
def update_route(dist, tt, ND, I, F, RI, RF, CTR, r):
    """Recompute positions, loads, cost and prefix/suffix segments of route r."""
    D, W, E, L = 0.0, 0.0, ND[TA, 0], ND[TB, 0]
    t = ND[TA, 0]
    last = 0
    load = 0.0
    cost = 0.0
    k = 0
    u = RI[FIRST, r]
    while u != 0:
        D, W, E, L = cat(D, W, E, L, ND[SVC, u], 0.0, ND[TA, u], ND[TB, u], tt[last, u])
        F[PD, u] = D
        F[PTW, u] = W
        F[PE, u] = E
        F[PL, u] = L
        t = t + tt[last, u]
        if t < ND[TA, u]:
            t = ND[TA, u]
        F[ES, u] = t
        t += ND[SVC, u]
        load += ND[DEM, u]
        F[PLOAD, u] = load
        cost += dist[last, u]
        I[RTE, u] = r
        I[POS, u] = k
        k += 1
        last = u
        u = I[NXT, u]
    RI[LAST, r] = last
    RI[LEN, r] = k
    RF[LOAD, r] = load
    if k == 0:
        RI[FIRST, r] = 0
        RF[COST, r] = 0.0
    else:
        RF[COST, r] = cost + dist[last, 0]
    D, W, E, L = 0.0, 0.0, ND[TA, 0], ND[TB, 0]
    nxt = 0
    u = last
    while u != 0:
        D, W, E, L = cat(ND[SVC, u], 0.0, ND[TA, u], ND[TB, u], D, W, E, L, tt[u, nxt])
        F[SD, u] = D
        F[STW, u] = W
        F[SE, u] = E
        F[SL, u] = L
        nxt = u
        u = I[PRV, u]
    CTR[0] += 1
    RI[STAMP, r] = CTR[0]


@njit
def set_route(dist, tt, ND, I, F, RI, RF, CTR, r, seq, m):
    """Make route r visit seq[0..m-1] in order."""
    prev = 0
    for k in range(m):
        u = seq[k]
        I[PRV, u] = prev
        if prev != 0:
            I[NXT, prev] = u
        prev = u
    if m > 0:
        I[NXT, prev] = 0
        RI[FIRST, r] = seq[0]
    else:
        RI[FIRST, r] = 0
    update_route(dist, tt, ND, I, F, RI, RF, CTR, r)


@njit
def collect(I, RI, r, buf):
    m = 0
    u = RI[FIRST, r]
    while u != 0:
        buf[m] = u
        m += 1
        u = I[NXT, u]
    return m


@njit
def unlink(I, RI, u):
    """Detach u from its route (route data become stale until update_route)."""
    r = I[RTE, u]
    p = I[PRV, u]
    x = I[NXT, u]
    if p == 0:
        RI[FIRST, r] = x
    else:
        I[NXT, p] = x
    if x != 0:
        I[PRV, x] = p
    I[RTE, u] = -1
    I[NXT, u] = 0
    I[PRV, u] = 0


@njit
def link_after(I, RI, u, v, r):
    """Insert detached u directly after v in route r (v == 0: at the start)."""
    if v == 0:
        x = RI[FIRST, r]
        RI[FIRST, r] = u
    else:
        x = I[NXT, v]
        I[NXT, v] = u
    I[PRV, u] = v
    I[NXT, u] = x
    if x != 0:
        I[PRV, x] = u
    I[RTE, u] = r


@njit
def seq_feasible(tt, ND, seq, m):
    """Earliest-schedule feasibility of one route visiting seq[0..m-1]."""
    t = ND[TA, 0]
    prev = 0
    for k in range(m):
        u = seq[k]
        t = t + tt[prev, u]
        if t < ND[TA, u]:
            t = ND[TA, u]
        if t > ND[TB, u] + EPS_TW:
            return False
        t += ND[SVC, u]
        prev = u
    return t + tt[prev, 0] <= ND[TB, 0] + EPS_TW


@njit
def seq_cost(dist, seq, m):
    if m == 0:
        return 0.0
    c = dist[0, seq[0]]
    for k in range(1, m):
        c += dist[seq[k - 1], seq[k]]
    return c + dist[seq[m - 1], 0]


@njit
def total_cost(RI, RF):
    c = 0.0
    for r in range(RI.shape[1]):
        if RI[LEN, r] > 0:
            c += RF[COST, r]
    return c


@njit
def refresh_score(I, RI, RF, SC):
    SC[0] = total_cost(RI, RF)
    un = 0
    for u in range(1, I.shape[1]):
        if I[RTE, u] < 0:
            un += 1
    SC[1] = un


@njit
def objective(SC, penalty):
    return SC[0] + penalty * SC[1]


@njit
def copy_sol(src, dst):
    dst[0][:, :] = src[0]
    dst[1][:, :] = src[1]
    dst[2][:, :] = src[2]
    dst[3][:, :] = src[3]
    dst[4][:, :] = src[4]
    dst[5][:] = src[5]


@njit
def used_routes(RI):
    k = 0
    for r in range(RI.shape[1]):
        if RI[LEN, r] > 0:
            k += 1
    return k


@njit
def empty_route(RI):
    for r in range(RI.shape[1]):
        if RI[LEN, r] == 0:
            return r
    return -1


@njit
def seed_rng(seed):
    np.random.seed(seed)


# ======================================================== VND moves =======
# All move functions evaluate the distance change first (O(1)), then capacity,
# then time windows: O(1) segment concatenation between routes, an exact
# O(route length) rebuild for intra-route moves.  They apply the move and
# return True only if it is feasible and strictly improving.

@njit
def try_relocate(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v, rv, buf):
    """Move u directly after v in route rv (v == 0: to the start of rv)."""
    ru = I[RTE, u]
    x = RI[FIRST, rv] if v == 0 else I[NXT, v]
    if v == u or x == u:
        return False
    pu = I[PRV, u]
    nu = I[NXT, u]
    delta = (dist[pu, nu] - dist[pu, u] - dist[u, nu]
             + dist[v, u] + dist[u, x] - dist[v, x])
    if delta > -EPS_COST:
        return False
    if ru != rv:
        if RF[LOAD, rv] + ND[DEM, u] > cap + EPS_LOAD:
            return False
        if insert_tw(tt, ND, F, v, u, x) > EPS_TW:
            return False
        if join_tw(tt, ND, F, pu, nu) > EPS_TW:
            return False
        unlink(I, RI, u)
        link_after(I, RI, u, v, rv)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, ru)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, rv)
        return True
    # intra-route: build the new order and verify it from scratch
    m = 0
    if v == 0:
        buf[m] = u
        m += 1
    y = RI[FIRST, ru]
    while y != 0:
        if y != u:
            buf[m] = y
            m += 1
            if y == v:
                buf[m] = u
                m += 1
        y = I[NXT, y]
    if not seq_feasible(tt, ND, buf, m):
        return False
    if seq_cost(dist, buf, m) > RF[COST, ru] - EPS_COST:
        return False
    set_route(dist, tt, ND, I, F, RI, RF, CTR, ru, buf, m)
    return True


@njit
def try_relocate_new_route(dist, tt, ND, I, F, RI, RF, CTR, empty_cost, u):
    """Move u alone into an unused route when that shortens the plan."""
    if empty_cost[u] >= INF:
        return False
    pu = I[PRV, u]
    nu = I[NXT, u]
    if pu == 0 and nu == 0:
        return False
    delta = dist[pu, nu] - dist[pu, u] - dist[u, nu] + empty_cost[u]
    if delta > -EPS_COST:
        return False
    r = empty_route(RI)
    if r < 0:
        return False
    if join_tw(tt, ND, F, pu, nu) > EPS_TW:
        return False
    ru = I[RTE, u]
    unlink(I, RI, u)
    link_after(I, RI, u, 0, r)
    update_route(dist, tt, ND, I, F, RI, RF, CTR, ru)
    update_route(dist, tt, ND, I, F, RI, RF, CTR, r)
    return True


@njit
def try_swap(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v, buf):
    ru = I[RTE, u]
    rv = I[RTE, v]
    pu = I[PRV, u]
    nu = I[NXT, u]
    pv = I[PRV, v]
    nv = I[NXT, v]
    if ru != rv:
        delta = (dist[pu, v] + dist[v, nu] - dist[pu, u] - dist[u, nu]
                 + dist[pv, u] + dist[u, nv] - dist[pv, v] - dist[v, nv])
        if delta > -EPS_COST:
            return False
        if RF[LOAD, ru] - ND[DEM, u] + ND[DEM, v] > cap + EPS_LOAD:
            return False
        if RF[LOAD, rv] - ND[DEM, v] + ND[DEM, u] > cap + EPS_LOAD:
            return False
        if insert_tw(tt, ND, F, pu, v, nu) > EPS_TW:
            return False
        if insert_tw(tt, ND, F, pv, u, nv) > EPS_TW:
            return False
        I[PRV, v] = pu
        I[NXT, v] = nu
        if pu == 0:
            RI[FIRST, ru] = v
        else:
            I[NXT, pu] = v
        if nu != 0:
            I[PRV, nu] = v
        I[PRV, u] = pv
        I[NXT, u] = nv
        if pv == 0:
            RI[FIRST, rv] = u
        else:
            I[NXT, pv] = u
        if nv != 0:
            I[PRV, nv] = u
        update_route(dist, tt, ND, I, F, RI, RF, CTR, ru)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, rv)
        return True
    if nu == v:
        delta = (dist[pu, v] + dist[v, u] + dist[u, nv]
                 - dist[pu, u] - dist[u, v] - dist[v, nv])
    elif nv == u:
        delta = (dist[pv, u] + dist[u, v] + dist[v, nu]
                 - dist[pv, v] - dist[v, u] - dist[u, nu])
    else:
        delta = (dist[pu, v] + dist[v, nu] - dist[pu, u] - dist[u, nu]
                 + dist[pv, u] + dist[u, nv] - dist[pv, v] - dist[v, nv])
    if delta > -EPS_COST:
        return False
    m = 0
    y = RI[FIRST, ru]
    while y != 0:
        if y == u:
            buf[m] = v
        elif y == v:
            buf[m] = u
        else:
            buf[m] = y
        m += 1
        y = I[NXT, y]
    if not seq_feasible(tt, ND, buf, m):
        return False
    if seq_cost(dist, buf, m) > RF[COST, ru] - EPS_COST:
        return False
    set_route(dist, tt, ND, I, F, RI, RF, CTR, ru, buf, m)
    return True


@njit
def try_two_opt_star(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v):
    """Inter-route tail exchange creating arc (u, v):
    route(u) := depot..u + v..depot,  route(v) := depot..prev(v) + next(u)..depot."""
    ru = I[RTE, u]
    rv = I[RTE, v]
    if ru == rv:
        return False
    pv = I[PRV, v]
    nu = I[NXT, u]
    delta = dist[u, v] + dist[pv, nu] - dist[u, nu] - dist[pv, v]
    if delta > -EPS_COST:
        return False
    head_u = pload(F, u)
    head_v = pload(F, pv)
    if head_u + (RF[LOAD, rv] - head_v) > cap + EPS_LOAD:
        return False
    if head_v + (RF[LOAD, ru] - head_u) > cap + EPS_LOAD:
        return False
    D1, W1, E1, L1 = pre(F, ND, u)
    D2, W2, E2, L2 = suf(F, ND, v)
    if cat(D1, W1, E1, L1, D2, W2, E2, L2, tt[u, v])[1] > EPS_TW:
        return False
    if join_tw(tt, ND, F, pv, nu) > EPS_TW:
        return False
    I[NXT, u] = v
    I[PRV, v] = u
    if pv == 0:
        RI[FIRST, rv] = nu
    else:
        I[NXT, pv] = nu
    if nu != 0:
        I[PRV, nu] = pv
    update_route(dist, tt, ND, I, F, RI, RF, CTR, ru)
    update_route(dist, tt, ND, I, F, RI, RF, CTR, rv)
    return True


@njit
def try_or_opt(dist, tt, ND, cap, sym, I, F, RI, RF, CTR, u, length, v, reverse, buf):
    """Move the string of ``length`` customers starting at u (following NXT).

    reverse == False: insert the string after v (creates arc v->u).
    reverse == True : insert it reversed before v (creates arc u->v).
    """
    if v == u:
        return False
    ru = I[RTE, u]
    rv = I[RTE, v]
    last = u
    sload = ND[DEM, u]
    for k in range(length - 1):
        last = I[NXT, last]
        if last == 0 or last == v:
            return False
        sload += ND[DEM, last]
    pf = I[PRV, u]
    nl = I[NXT, last]
    # The string goes between a and b.  With v outside the string the removed
    # arcs (pf,u), (last,nl), (a,b) are distinct, so the arc formula below is
    # exact; the only degenerate placements are excluded here.
    if not reverse:
        a = v
        b = I[NXT, v]
        if a == pf:
            return False          # already there
    else:
        a = I[PRV, v]
        b = v
        if b == nl:
            return False          # in-place reversal: covered by 2-opt
    rem = dist[pf, nl] - dist[pf, u] - dist[last, nl]
    if not reverse:
        delta = rem + dist[a, u] + dist[last, b] - dist[a, b]
    else:
        delta = rem + dist[a, last] + dist[u, b] - dist[a, b]
        if sym == 0:
            c_fwd = chain_seg(dist, tt, ND, I, u, length, False)[4]
            c_rev = chain_seg(dist, tt, ND, I, u, length, True)[4]
            delta += c_rev - c_fwd
    if delta > -EPS_COST:
        return False
    if ru != rv:
        if RF[LOAD, rv] + sload > cap + EPS_LOAD:
            return False
        Ds, Ws, Es, Ls, _ = chain_seg(dist, tt, ND, I, u, length, reverse)
        if Ws > EPS_TW:
            return False
        s_first = last if reverse else u
        s_last = u if reverse else last
        D, W, E, L = pre(F, ND, a)
        D, W, E, L = cat(D, W, E, L, Ds, Ws, Es, Ls, tt[a, s_first])
        D2, W2, E2, L2 = suf(F, ND, b)
        if cat(D, W, E, L, D2, W2, E2, L2, tt[s_last, b])[1] > EPS_TW:
            return False
        if join_tw(tt, ND, F, pf, nl) > EPS_TW:
            return False
        # detach the string, then relink it between a and b
        if pf == 0:
            RI[FIRST, ru] = nl
        else:
            I[NXT, pf] = nl
        if nl != 0:
            I[PRV, nl] = pf
        prev = a
        x = s_first
        for k in range(length):
            y = I[PRV, x] if reverse else I[NXT, x]
            link_after(I, RI, x, prev, rv)
            prev = x
            x = y
        update_route(dist, tt, ND, I, F, RI, RF, CTR, ru)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, rv)
        return True
    # intra-route: rebuild the sequence and verify it exactly
    m = 0
    if a == 0:
        m = _emit_string(I, u, last, length, reverse, buf, m)
    y = RI[FIRST, ru]
    while y != 0:
        if y == u:
            y = nl            # skip the string
            continue
        buf[m] = y
        m += 1
        if y == a:
            m = _emit_string(I, u, last, length, reverse, buf, m)
        y = I[NXT, y]
    if not seq_feasible(tt, ND, buf, m):
        return False
    if seq_cost(dist, buf, m) > RF[COST, ru] - EPS_COST:
        return False
    set_route(dist, tt, ND, I, F, RI, RF, CTR, ru, buf, m)
    return True


@njit
def _emit_string(I, u, last, length, reverse, buf, m):
    x = last if reverse else u
    for k in range(length):
        buf[m] = x
        m += 1
        x = I[PRV, x] if reverse else I[NXT, x]
    return m


@njit
def try_two_opt(dist, tt, ND, sym, I, F, RI, RF, CTR, u, v, buf):
    """Intra-route 2-opt creating arc (u, v): reverse the path between them."""
    r = I[RTE, u]
    if I[RTE, v] != r or u == v:
        return False
    if I[POS, u] < I[POS, v]:
        x = u
        y = v
    else:
        x = v
        y = u
    nx = I[NXT, x]
    ny = I[NXT, y]
    if nx == y:
        return False
    if sym == 1:
        delta = dist[x, y] + dist[nx, ny] - dist[x, nx] - dist[y, ny]
        if delta > -EPS_COST:
            return False
    m = collect(I, RI, r, buf)
    i = I[POS, nx]
    j = I[POS, y]
    while i < j:
        tmp = buf[i]
        buf[i] = buf[j]
        buf[j] = tmp
        i += 1
        j -= 1
    if not seq_feasible(tt, ND, buf, m):
        return False
    if seq_cost(dist, buf, m) > RF[COST, r] - EPS_COST:
        return False
    set_route(dist, tt, ND, I, F, RI, RF, CTR, r, buf, m)
    return True


@njit
def vnd(inst, sol, order, G, buf):
    """Variable Neighbourhood Descent over granular neighbourhoods.

    Neighbourhoods are explored in ``order``; a pass of neighbourhood k over
    every customer u and its first G neighbours v applies every improving move
    found (first improvement).  After a pass with an improvement the descent
    restarts at the first neighbourhood, otherwise it moves on to the next one;
    it stops when a full sweep finds nothing, i.e. at a local optimum of all
    neighbourhoods.

    Modification stamps skip (u, v) pairs whose two routes are unchanged since u
    was last examined in that neighbourhood, so re-optimising a solution after
    an ALNS destroy/repair only re-examines the affected region.
    """
    dist, tt, ND, cap, nbrs, sym, empty_cost = inst[0], inst[1], inst[2], inst[3], inst[4], inst[7], inst[8]
    I, F, RI, RF, TST, SC, CTR = sol[0], sol[1], sol[2], sol[3], sol[4], sol[5], sol[6]
    N = I.shape[1]
    if G > nbrs.shape[1]:
        G = nbrs.shape[1]
    perm = np.random.permutation(N - 1) + 1
    k = 0
    n_moves = 0
    while k < order.shape[0]:
        nb = order[k]
        improved = False
        for idx in range(N - 1):
            u = perm[idx]
            if I[RTE, u] < 0:
                continue
            last_tested = TST[nb, u]
            TST[nb, u] = CTR[0]
            if nb == NB_RELOCATE and RI[STAMP, I[RTE, u]] > last_tested:
                if try_relocate_new_route(dist, tt, ND, I, F, RI, RF, CTR, empty_cost, u):
                    improved = True
                    n_moves += 1
            for jj in range(G):
                v = nbrs[u, jj]
                rv = I[RTE, v]
                if rv < 0:
                    continue
                ru = I[RTE, u]
                if RI[STAMP, ru] <= last_tested and RI[STAMP, rv] <= last_tested:
                    continue
                moved = False
                if nb == NB_RELOCATE:
                    moved = try_relocate(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v, rv, buf)
                    if not moved:
                        moved = try_relocate(dist, tt, ND, cap, I, F, RI, RF, CTR, u, I[PRV, v], rv, buf)
                elif nb == NB_SWAP:
                    moved = try_swap(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v, buf)
                elif nb == NB_TWO_OPT_STAR:
                    if rv != ru:
                        moved = try_two_opt_star(dist, tt, ND, cap, I, F, RI, RF, CTR, u, v)
                        if not moved:
                            moved = try_two_opt_star(dist, tt, ND, cap, I, F, RI, RF, CTR, v, u)
                elif nb == NB_OR_OPT:
                    for length in range(2, 4):
                        moved = try_or_opt(dist, tt, ND, cap, sym, I, F, RI, RF, CTR, u, length, v, False, buf)
                        if moved:
                            break
                        moved = try_or_opt(dist, tt, ND, cap, sym, I, F, RI, RF, CTR, u, length, v, True, buf)
                        if moved:
                            break
                elif nb == NB_TWO_OPT:
                    if rv == ru:
                        moved = try_two_opt(dist, tt, ND, sym, I, F, RI, RF, CTR, u, v, buf)
                if moved:
                    improved = True
                    n_moves += 1
        if improved:
            k = 0
        else:
            k += 1
    refresh_score(I, RI, RF, SC)
    return n_moves


# ======================================================== insertion =======
@njit
def best_insertion(dist, tt, ND, cap, I, F, RI, RF, u, r, blink):
    """Cheapest feasible position of unassigned u in nonempty route r.

    Returns (delta_cost, predecessor) or (INF, -1).  Each position is skipped
    with probability ``blink`` (SISR "blinks")."""
    if RF[LOAD, r] + ND[DEM, u] > cap + EPS_LOAD:
        return INF, -1
    best = INF
    bp = -1
    p = 0
    x = RI[FIRST, r]
    late_u = ND[TB, u] + EPS_TW
    while True:
        # Earliest service starts grow along the route; once u can no longer be
        # reached in time from p it cannot be from later nodes (metric travel).
        if p != 0 and F[ES, p] + ND[SVC, p] + tt[p, u] > late_u:
            break
        delta = dist[p, u] + dist[u, x] - dist[p, x]
        if delta < best:
            if blink <= 0.0 or np.random.random() >= blink:
                if insert_tw(tt, ND, F, p, u, x) <= EPS_TW:
                    best = delta
                    bp = p
        if x == 0:
            break
        p = x
        x = I[NXT, x]
    return best, bp


@njit
def repair_regret(inst, sol, pool, m, k, blink, insert_all):
    """Regret-k insertion (k == 1: parallel cheapest insertion).

    Customers pool[0..m-1] are inserted one by one; at each step the customer
    with the largest regret  sum_{h=2..k} (c_h - c_1)  over its k best routes is
    inserted at its cheapest position (ties: lower c_1).  Insertion costs are
    cached per (customer, route) and invalidated only for the modified route.
    Candidate routes are those of the customer's granular neighbours plus one
    unused route; if none admits the customer every route is scanned.

    Returns the number of customers left unassigned (moved to pool[0..])."""
    dist, tt, ND, cap, nbrs, empty_cost = inst[0], inst[1], inst[2], inst[3], inst[4], inst[8]
    I, F, RI, RF, CTR = sol[0], sol[1], sol[2], sol[3], sol[6]
    R = RI.shape[1]
    G = nbrs.shape[1]
    cost = np.empty((m, R))
    prv = np.empty((m, R), np.int64)
    valid = np.zeros((m, R), np.bool_)
    alive = np.ones(m, np.bool_)
    mark = np.zeros(R, np.int64)
    stamp = 0
    used = used_routes(RI)
    remaining = m
    while remaining > 0:
        best_i = -1
        best_score = -INF
        best_c1 = INF
        best_r = -1
        best_p = -1
        for i in range(m):
            if not alive[i]:
                continue
            u = pool[i]
            c1 = INF
            c2 = INF
            c3 = INF
            r1 = -1
            p1 = -1
            stamp += 1
            scan_all = insert_all == 1
            for phase in range(2):
                if phase == 1 and not scan_all:
                    break
                for jj in range(R if phase == 1 else G):
                    if phase == 0:
                        if insert_all == 1:
                            break
                        r = I[RTE, nbrs[u, jj]]
                    else:
                        r = jj
                    if r < 0 or mark[r] == stamp or RI[LEN, r] == 0:
                        continue
                    mark[r] = stamp
                    if not valid[i, r]:
                        c, p = best_insertion(dist, tt, ND, cap, I, F, RI, RF, u, r, blink)
                        cost[i, r] = c
                        prv[i, r] = p
                        valid[i, r] = True
                    c = cost[i, r]
                    if c < c1:
                        c3 = c2
                        c2 = c1
                        c1 = c
                        r1 = r
                        p1 = prv[i, r]
                    elif c < c2:
                        c3 = c2
                        c2 = c
                    elif c < c3:
                        c3 = c
                if phase == 0 and c1 >= INF:
                    scan_all = True
            if used < R and empty_cost[u] < INF:
                c = empty_cost[u]
                if c < c1:
                    c3 = c2
                    c2 = c1
                    c1 = c
                    r1 = -2
                    p1 = 0
                elif c < c2:
                    c3 = c2
                    c2 = c
                elif c < c3:
                    c3 = c
            if c1 >= INF:
                # no feasible position anywhere: inserting others only tightens
                # routes, so u stays unassigned for this repair.
                alive[i] = False
                remaining -= 1
                continue
            if k <= 1:
                score = -c1
            else:
                score = (c2 - c1) if c2 < INF else BIG_REGRET
                if k >= 3:
                    score += (c3 - c1) if c3 < INF else BIG_REGRET
            if score > best_score or (score == best_score and c1 < best_c1):
                best_score = score
                best_c1 = c1
                best_i = i
                best_r = r1
                best_p = p1
        if best_i < 0:
            break
        u = pool[best_i]
        if best_r == -2:
            best_r = empty_route(RI)
            used += 1
        link_after(I, RI, u, best_p, best_r)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, best_r)
        alive[best_i] = False
        remaining -= 1
        for i in range(m):
            valid[i, best_r] = False
    left = 0
    for i in range(m):
        if I[RTE, pool[i]] < 0:
            pool[left] = pool[i]
            left += 1
    return left


@njit
def repair_blink(inst, sol, pool, m, blink, insert_all):
    """SISR-style greedy insertion with blinks in a randomly chosen order
    (random / largest demand / farthest from depot / closest / tightest window)."""
    dist, tt, ND, cap, nbrs, empty_cost = inst[0], inst[1], inst[2], inst[3], inst[4], inst[8]
    I, F, RI, RF, CTR = sol[0], sol[1], sol[2], sol[3], sol[6]
    R = RI.shape[1]
    G = nbrs.shape[1]
    key = np.empty(m)
    rule = np.random.random()
    for i in range(m):
        u = pool[i]
        if rule < 0.4:
            key[i] = np.random.random()
        elif rule < 0.7:
            key[i] = -ND[DEM, u]
        elif rule < 0.85:
            key[i] = -dist[0, u]
        elif rule < 0.9:
            key[i] = dist[0, u]
        else:
            key[i] = ND[TB, u] - ND[TA, u]
    order = np.argsort(key)
    tmp = pool[:m].copy()
    for i in range(m):
        pool[i] = tmp[order[i]]
    mark = np.zeros(R, np.int64)
    used = used_routes(RI)
    for i in range(m):
        u = pool[i]
        best = INF
        br = -1
        bp = -1
        scan_all = insert_all == 1
        for phase in range(2):
            if phase == 1 and not scan_all:
                break
            for jj in range(R if phase == 1 else G):
                if phase == 0:
                    if insert_all == 1:
                        break
                    r = I[RTE, nbrs[u, jj]]
                else:
                    r = jj
                if r < 0 or mark[r] == i + 1 or RI[LEN, r] == 0:
                    continue
                mark[r] = i + 1
                c, p = best_insertion(dist, tt, ND, cap, I, F, RI, RF, u, r, blink)
                if c < best:
                    best = c
                    br = r
                    bp = p
            if phase == 0 and best >= INF:
                scan_all = True
        if used < R and empty_cost[u] < best:
            best = empty_cost[u]
            br = -2
            bp = 0
        if best >= INF:
            continue
        if br == -2:
            br = empty_route(RI)
            used += 1
        link_after(I, RI, u, bp, br)
        update_route(dist, tt, ND, I, F, RI, RF, CTR, br)
    left = 0
    for i in range(m):
        if I[RTE, pool[i]] < 0:
            pool[left] = pool[i]
            left += 1
    return left


# ========================================================== destroy =======
@njit
def remove_customer(I, RI, u, pool, m, dirty):
    dirty[I[RTE, u]] = True
    unlink(I, RI, u)
    pool[m] = u
    return m + 1


@njit
def random_assigned(I):
    N = I.shape[1]
    for _ in range(64):
        u = np.random.randint(1, N)
        if I[RTE, u] >= 0:
            return u
    for u in range(1, N):
        if I[RTE, u] >= 0:
            return u
    return -1


@njit
def destroy_random(I, RI, pool, m, q, dirty):
    N = I.shape[1]
    cand = np.random.permutation(N - 1) + 1
    removed = 0
    for idx in range(N - 1):
        if removed >= q:
            break
        u = cand[idx]
        if I[RTE, u] >= 0:
            m = remove_customer(I, RI, u, pool, m, dirty)
            removed += 1
    return m


@njit
def destroy_worst(dist, I, RI, pool, m, q, dirty, p_worst):
    """Ropke & Pisinger worst removal: rank by distance saving, pick rank y^p."""
    N = I.shape[1]
    nodes = np.empty(N - 1, np.int64)
    gain = np.empty(N - 1)
    k = 0
    for u in range(1, N):
        if I[RTE, u] >= 0:
            p = I[PRV, u]
            x = I[NXT, u]
            nodes[k] = u
            gain[k] = -(dist[p, u] + dist[u, x] - dist[p, x])
            k += 1
    order = np.argsort(gain[:k])
    taken = np.zeros(k, np.bool_)
    left = k
    removed = 0
    while removed < q and left > 0:
        idx = int(np.random.random() ** p_worst * left)
        c = -1
        for j in range(k):
            if not taken[j]:
                c += 1
                if c == idx:
                    taken[j] = True
                    m = remove_customer(I, RI, nodes[order[j]], pool, m, dirty)
                    break
        left -= 1
        removed += 1
    return m


@njit
def destroy_shaw(shaw, I, RI, pool, m, q, dirty, p_shaw):
    """Shaw (relatedness) removal using precomputed relatedness lists."""
    L = shaw.shape[1]
    start = m
    seed = random_assigned(I)
    if seed < 0:
        return m
    m = remove_customer(I, RI, seed, pool, m, dirty)
    removed = 1
    cand = np.empty(max(L, 1), np.int64)
    while removed < q:
        r = pool[start + np.random.randint(0, m - start)]
        c = 0
        for j in range(L):
            v = shaw[r, j]
            if I[RTE, v] >= 0:
                cand[c] = v
                c += 1
        if c == 0:
            v = random_assigned(I)
            if v < 0:
                break
        else:
            v = cand[int(np.random.random() ** p_shaw * c)]
        m = remove_customer(I, RI, v, pool, m, dirty)
        removed += 1
    return m


@njit
def destroy_string(near, I, RI, pool, m, dirty, cbar, lmax, split_prob, beta, buf):
    """SISR string removal (Christiaens & Vanden Berghe, 2020): remove strings
    (optionally split around a preserved substring) from routes adjacent to a
    random seed customer.  Its size is governed by cbar/lmax, not by q."""
    R = RI.shape[1]
    nonempty = 0
    assigned = 0
    for r in range(R):
        if RI[LEN, r] > 0:
            nonempty += 1
            assigned += RI[LEN, r]
    if nonempty == 0:
        return m
    ls_max = min(float(lmax), assigned / nonempty)
    ks_max = 4.0 * cbar / (1.0 + ls_max) - 1.0
    ks = int(np.random.random() * ks_max) + 1
    seed = random_assigned(I)
    ruined = np.zeros(R, np.bool_)
    n_ruined = 0
    for j in range(-1, near.shape[1]):
        if n_ruined >= ks:
            break
        c = seed if j < 0 else near[seed, j]
        r = I[RTE, c]
        if r < 0 or ruined[r]:
            continue
        ruined[r] = True
        n_ruined += 1
        t = collect(I, RI, r, buf)
        lt_max = min(float(t), ls_max)
        l = int(np.random.random() * lt_max) + 1
        pc = I[POS, c]
        keep = 0
        if np.random.random() < split_prob and l < t:
            keep = 1
            while l + keep < t and np.random.random() > beta:
                keep += 1
        total = l + keep
        lo = max(0, pc - total + 1)
        hi = min(pc, t - total)
        s = lo + np.random.randint(0, hi - lo + 1)
        keep_start = s + np.random.randint(0, l + 1) if keep > 0 else -1
        for k in range(s, s + total):
            if keep > 0 and keep_start <= k < keep_start + keep:
                continue
            m = remove_customer(I, RI, buf[k], pool, m, dirty)
    return m


@njit
def destroy_route(I, RI, pool, m, dirty):
    """Remove all customers of one random route (route-count reduction)."""
    R = RI.shape[1]
    nonempty = 0
    for r in range(R):
        if RI[LEN, r] > 0:
            nonempty += 1
    if nonempty == 0:
        return m
    pick = np.random.randint(0, nonempty)
    for r in range(R):
        if RI[LEN, r] > 0:
            if pick == 0:
                u = RI[FIRST, r]
                while u != 0:
                    x = I[NXT, u]
                    m = remove_customer(I, RI, u, pool, m, dirty)
                    u = x
                break
            pick -= 1
    return m


# ===================================================== ALNS main loop ======
@njit
def roulette(w):
    total = 0.0
    for i in range(w.shape[0]):
        total += w[i]
    x = np.random.random() * total
    for i in range(w.shape[0]):
        x -= w[i]
        if x <= 0.0 and w[i] > 0.0:
            return i
    for i in range(w.shape[0] - 1, -1, -1):
        if w[i] > 0.0:
            return i
    return 0


@njit
def construct(inst, sol, pool, order, G):
    """Initial solution: parallel cheapest insertion of every customer
    (regret-1, granular candidate routes), followed by VND."""
    I, RI, RF, SC = sol[0], sol[2], sol[3], sol[5]
    N = I.shape[1]
    m = 0
    for u in range(1, N):
        if I[RTE, u] < 0:
            pool[m] = u
            m += 1
    repair_regret(inst, sol, pool, m, 1, 0.0, 0)
    refresh_score(I, RI, RF, SC)
    buf = np.empty(N, np.int64)
    if SC[1] == 0:
        vnd(inst, sol, order, G, buf)
    refresh_score(I, RI, RF, SC)


@njit
def alns_chunk(inst, cur, cand, best, IP, P, wd, wr, sd, sr, ud, ur,
               order, n_iter, temperature, stats, pool, buf):
    """Run ``n_iter`` ALNS iterations (destroy, repair, VND, SA acceptance)."""
    dist, tt, ND, near, shaw = inst[0], inst[1], inst[2], inst[5], inst[6]
    cI, cF, cRI, cRF, cCTR = cand[0], cand[1], cand[2], cand[3], cand[6]
    N = cI.shape[1]
    R = cRI.shape[1]
    penalty = P[P_PENALTY]
    G = IP[IP_VND_NEIGHBOURS]
    dirty = np.zeros(R, np.bool_)
    for _ in range(n_iter):
        IP[IP_ITER] += 1
        it = IP[IP_ITER]
        copy_sol(cur, cand)
        d = roulette(wd)
        rp = roulette(wr)
        q = IP[IP_QMIN]
        if IP[IP_QMAX] > IP[IP_QMIN]:
            q = np.random.randint(IP[IP_QMIN], IP[IP_QMAX] + 1)
        # customers still unassigned stay in the pool
        m = 0
        for u in range(1, N):
            if cI[RTE, u] < 0:
                pool[m] = u
                m += 1
        dirty[:] = False
        if d == D_RANDOM:
            m = destroy_random(cI, cRI, pool, m, q, dirty)
        elif d == D_WORST:
            m = destroy_worst(dist, cI, cRI, pool, m, q, dirty, P[P_WORST_P])
        elif d == D_SHAW:
            m = destroy_shaw(shaw, cI, cRI, pool, m, q, dirty, P[P_SHAW_P])
        elif d == D_STRING:
            m = destroy_string(near, cI, cRI, pool, m, dirty, P[P_SISR_CBAR],
                               IP[IP_SISR_LMAX], P[P_SISR_SPLIT], P[P_SISR_BETA], buf)
        else:
            m = destroy_route(cI, cRI, pool, m, dirty)
        for r in range(R):
            if dirty[r]:
                update_route(dist, tt, ND, cI, cF, cRI, cRF, cCTR, r)
        if rp == R_GREEDY:
            left = repair_regret(inst, cand, pool, m, 1, 0.0, IP[IP_INSERT_ALL])
        elif rp == R_REGRET2:
            left = repair_regret(inst, cand, pool, m, 2, 0.0, IP[IP_INSERT_ALL])
        elif rp == R_REGRET3:
            left = repair_regret(inst, cand, pool, m, 3, 0.0, IP[IP_INSERT_ALL])
        else:
            left = repair_blink(inst, cand, pool, m, P[P_BLINK], IP[IP_INSERT_ALL])
        refresh_score(cI, cRI, cRF, cand[5])
        if left == 0:
            stats[ST_VND_MOVES] += vnd(inst, cand, order, G, buf)
        else:
            stats[ST_INFEASIBLE_CAND] += 1
        f_cand = objective(cand[5], penalty)
        f_cur = objective(cur[5], penalty)
        f_best = objective(best[5], penalty)
        score = 0.0
        if f_cand < f_best - EPS_COST:
            copy_sol(cand, best)
            copy_sol(cand, cur)
            score = P[P_SIG1]
            IP[IP_LAST_IMPROVE] = it
            stats[ST_NEW_BEST] += 1
            stats[ST_ACCEPT] += 1
        elif f_cand < f_cur - EPS_COST:
            copy_sol(cand, cur)
            score = P[P_SIG2]
            stats[ST_IMPROVE_CUR] += 1
            stats[ST_ACCEPT] += 1
        elif f_cand <= f_cur + EPS_COST:
            copy_sol(cand, cur)          # sideways move: accept, no reward
            stats[ST_ACCEPT] += 1
        elif temperature > 0.0:
            if np.random.random() < np.exp(-(f_cand - f_cur) / temperature):
                copy_sol(cand, cur)
                score = P[P_SIG3]
                stats[ST_ACCEPT] += 1
        sd[d] += score
        ud[d] += 1.0
        sr[rp] += score
        ur[rp] += 1.0
        stats[ST_ITERS] += 1
        if IP[IP_SEGMENT] > 0 and it % IP[IP_SEGMENT] == 0:
            rho = P[P_REACTION]
            for j in range(wd.shape[0]):
                if wd[j] > 0.0 and ud[j] > 0.0:
                    wd[j] = max(1e-3, wd[j] * (1.0 - rho) + rho * sd[j] / ud[j])
                sd[j] = 0.0
                ud[j] = 0.0
            for j in range(wr.shape[0]):
                if wr[j] > 0.0 and ur[j] > 0.0:
                    wr[j] = max(1e-3, wr[j] * (1.0 - rho) + rho * sr[j] / ur[j])
                sr[j] = 0.0
                ur[j] = 0.0
        if IP[IP_RESTART] > 0 and it - IP[IP_LAST_IMPROVE] >= IP[IP_RESTART]:
            copy_sol(best, cur)
            IP[IP_LAST_IMPROVE] = it
            stats[ST_RESTARTS] += 1
