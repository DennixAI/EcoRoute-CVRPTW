"""ALNS + VND driver: preprocessing, time management, trace and result packaging.

Public entry point: ``solve(instance, config, seed, time_limit) -> SolverResult``,
matching the ``scripts.benchmark.Solver`` protocol.  The solver receives only the
instance (never reference routes or costs), returns customer-only routes in
internal indices 1..n, and lets the shared evaluator re-check everything.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import time

import numpy as np

from scripts.benchmark import SolverResult
from scripts.cvrptw_model import CVRPTWInstance, require_cvrptw

from . import kernels as K
from ._jit import JIT_ENABLED
from .config import ALNSConfig, DESTROY_OPERATORS, NEIGHBOURHOODS, REPAIR_OPERATORS

VERSION = "alns-vnd-1.0"
_SOURCES = ("__init__.py", "_jit.py", "config.py", "kernels.py", "solver.py")


# Set by the main.ipynb loader when the solver was compiled from notebook cells
# that differ from these files: {module: sha256 of the notebook source}.
NOTEBOOK_SOURCE_SHA256 = None


def source_fingerprint():
    """SHA256 of the solver sources (recorded with every run)."""
    if NOTEBOOK_SOURCE_SHA256 is not None:
        return {"origin": "main.ipynb", **NOTEBOOK_SOURCE_SHA256}
    root = Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in _SOURCES}


def _process_start():
    """Monotonic-clock estimate of when this process started (or None)."""
    try:
        import psutil
        age = time.time() - psutil.Process(os.getpid()).create_time()
        return time.perf_counter() - max(0.0, age)
    except Exception:
        return None


# ----------------------------------------------------------- preprocessing --
def _top_k(score, k):
    """Indices of the k smallest entries of each row (row-wise, sorted)."""
    if k <= 0:
        return np.zeros((score.shape[0], 0), np.int64)
    part = np.argpartition(score, k - 1, axis=1)[:, :k]
    rows = np.arange(score.shape[0])[:, None]
    order = np.argsort(score[rows, part], axis=1, kind="stable")
    return np.ascontiguousarray(part[rows, order], dtype=np.int64)


def build_instance_data(instance: CVRPTWInstance, cfg: ALNSConfig):
    """Numba-ready tuple with distances, windows and neighbour lists."""
    dist = np.ascontiguousarray(instance.distances, dtype=np.float64)
    tt = np.ascontiguousarray(instance.travel_times, dtype=np.float64)
    ta = np.ascontiguousarray(instance.time_windows[:, 0], dtype=np.float64)
    tb = np.ascontiguousarray(instance.time_windows[:, 1], dtype=np.float64)
    svc = np.ascontiguousarray(instance.service_durations, dtype=np.float64)
    dem = np.ascontiguousarray(instance.demands, dtype=np.float64)
    N = dem.shape[0]
    n = N - 1
    cap = float(instance.capacity)
    sym = int(np.array_equal(dist, dist.T) and np.array_equal(tt, tt.T))

    # Depot -> u -> depot (earliest schedule); INF when u cannot be served alone.
    arrive = np.maximum(ta[0] + tt[0, :], ta)
    alone_ok = (arrive <= tb + K.EPS_TW) & (arrive + svc + tt[:, 0] <= tb[0] + K.EPS_TW)
    empty_cost = np.where(alone_ok, dist[0, :] + dist[:, 0], K.INF)
    empty_cost[0] = K.INF

    c = slice(1, N)
    # Granular proximity (Vidal et al. 2013): distance plus penalties for the
    # waiting / lateness incurred if j directly follows i.
    late = np.maximum(ta[c, None] + svc[c, None] + tt[c, c] - tb[None, c], 0.0)
    wait = np.maximum(ta[None, c] - svc[c, None] - tt[c, c] - tb[c, None], 0.0)
    prox = dist[c, c] + cfg.tw_wait_weight * wait + cfg.tw_warp_weight * late
    prox = np.minimum(prox, prox.T)
    np.fill_diagonal(prox, np.inf)
    G = min(cfg.n_neighbours, n - 1)
    nbrs = np.zeros((N, G), np.int64)
    nbrs[1:] = _top_k(prox, G) + 1

    d_sym = np.minimum(dist[c, c], dist[c, c].T).copy()
    np.fill_diagonal(d_sym, np.inf)
    near = np.zeros((N, min(cfg.near_list, n - 1)), np.int64)
    near[1:] = _top_k(d_sym, near.shape[1]) + 1

    w_d, w_t, w_q = cfg.shaw_weights
    dmax = max(float(np.max(dist[c, c])), 1e-12)
    tspan = max(float(tb[c].max() - ta[c].min()), 1e-12)
    qmax = max(float(dem[c].max()), 1e-12)
    related = (w_d * d_sym / dmax
               + w_t * (np.abs(ta[c, None] - ta[None, c]) + np.abs(tb[c, None] - tb[None, c])) / (2 * tspan)
               + w_q * np.abs(dem[c, None] - dem[None, c]) / qmax)
    np.fill_diagonal(related, np.inf)
    shaw = np.zeros((N, min(cfg.shaw_list, n - 1)), np.int64)
    shaw[1:] = _top_k(related, shaw.shape[1]) + 1

    ND = np.ascontiguousarray(np.vstack([ta, tb, svc, dem]), dtype=np.float64)
    return (dist, tt, ND, cap, nbrs, near, shaw, sym,
            np.ascontiguousarray(empty_cost, dtype=np.float64))


def new_solution(N, R, ctr):
    I = np.zeros((4, N), np.int64)
    I[K.RTE, :] = -1
    I[K.RTE, 0] = -2  # depot is never a customer
    F = np.zeros((10, N), np.float64)
    RI = np.zeros((4, R), np.int64)
    RF = np.zeros((2, R), np.float64)
    TST = np.zeros((K.N_NEIGHBOURHOODS, N), np.int64)
    SC = np.zeros(2, np.float64)
    SC[1] = N - 1
    return (I, F, RI, RF, TST, SC, ctr)


def decode_routes(sol):
    I, RI = sol[0], sol[2]
    routes = []
    for r in range(RI.shape[1]):
        if RI[K.LEN, r] == 0:
            continue
        route = []
        u = int(RI[K.FIRST, r])
        while u != 0:
            route.append(u)
            u = int(I[K.NXT, u])
        routes.append(route)
    return routes


def route_cost(instance, routes):
    """Claimed cost with the instance's own scoring (DIMACS integer tenths when cached)."""
    ticks = instance.distance_tenths
    if ticks is not None:
        total = 0
        for r in routes:
            path = [0] + r + [0]
            total += int(sum(int(ticks[i, j]) for i, j in zip(path, path[1:])))
        return total / 10
    return float(sum(instance.distances[i, j] for r in routes for i, j in zip([0] + r, r + [0])))


# ------------------------------------------------------------------- solve --
def solve(instance: CVRPTWInstance, config: dict | None, seed: int, time_limit: float) -> SolverResult:
    """Run ALNS + VND under a wall-clock limit (seconds) and return the best
    feasible solution found.  ``config`` overrides ALNSConfig defaults."""
    call_start = time.perf_counter()
    require_cvrptw(instance)
    cfg = ALNSConfig.from_dict(config)
    if not np.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be positive and finite")
    origin = _process_start()
    if cfg.clock == "process":
        if origin is None:
            raise RuntimeError("clock='process' requires psutil to read the process start time")
        budget_origin = min(origin, call_start)
    else:
        budget_origin = call_start
    deadline = budget_origin + time_limit * cfg.time_fraction - cfg.time_reserve
    if deadline <= call_start:
        deadline = call_start + 0.5 * time_limit * cfg.time_fraction

    seed = int(seed)
    K.seed_rng(seed % (2 ** 32))
    inst = build_instance_data(instance, cfg)
    N = inst[2].shape[1]
    n = N - 1
    R = int(min(instance.max_vehicles, n))
    ctr = np.zeros(1, np.int64)
    cur = new_solution(N, R, ctr)
    cand = new_solution(N, R, ctr)
    best = new_solution(N, R, ctr)
    order = np.array([NEIGHBOURHOODS.index(nb) for nb in cfg.neighbourhoods], np.int64)
    pool = np.zeros(N, np.int64)
    buf = np.zeros(N, np.int64)

    K.construct(inst, cur, pool, order, cfg.vnd_neighbours)
    K.copy_sol(cur, best)
    construct_seconds = time.perf_counter() - call_start
    initial_cost = float(cur[5][0])
    initial_unassigned = int(cur[5][1])

    max_dist = float(np.max(inst[0])) if n else 0.0
    penalty = 1e3 * (1.0 + 2.0 * max_dist)
    q_max = int(max(1, min(cfg.destroy_max, round(cfg.destroy_max_fraction * n), n)))
    q_min = int(min(cfg.destroy_min, q_max))
    IP = np.zeros(K.N_IP, np.int64)
    IP[K.IP_QMIN], IP[K.IP_QMAX] = q_min, q_max
    IP[K.IP_SEGMENT], IP[K.IP_RESTART] = cfg.segment, cfg.restart_after
    IP[K.IP_SISR_LMAX] = cfg.sisr_max_string
    IP[K.IP_INSERT_ALL] = int(cfg.insert_all_routes)
    IP[K.IP_VND_NEIGHBOURS] = cfg.vnd_neighbours
    P = np.zeros(K.N_P, np.float64)
    P[K.P_WORST_P], P[K.P_SHAW_P] = cfg.worst_randomness, cfg.shaw_randomness
    P[K.P_SISR_CBAR], P[K.P_SISR_SPLIT], P[K.P_SISR_BETA] = cfg.sisr_avg_removed, cfg.sisr_split_rate, cfg.sisr_split_depth
    P[K.P_BLINK] = cfg.blink_rate
    P[K.P_SIG1], P[K.P_SIG2], P[K.P_SIG3] = cfg.score_new_best, cfg.score_better, cfg.score_accepted
    P[K.P_REACTION], P[K.P_PENALTY] = cfg.reaction, penalty
    wd = np.array(cfg.destroy_weights, np.float64)
    wr = np.array(cfg.repair_weights, np.float64)
    sd, ud = np.zeros_like(wd), np.zeros_like(wd)
    sr, ur = np.zeros_like(wr), np.zeros_like(wr)
    stats = np.zeros(K.N_ST, np.float64)

    used = max(1, K.used_routes(cur[2]))
    mean_arc = initial_cost / (n + used) if n else 1.0
    t_start = cfg.temp_start * mean_arc
    t_end = cfg.temp_end * mean_arc

    def best_cost():
        return float(best[5][0]) if best[5][1] == 0 else None

    trace = [dict(seconds=round(time.perf_counter() - budget_origin, 4), iteration=0,
                  best_cost=best_cost(), current_cost=float(cur[5][0]), event="construction")]
    chunk = 1
    stop_reason = "time_limit"
    last_best = objective = K.objective(best[5], penalty)
    time_to_best = time.perf_counter() - budget_origin
    last_trace = time.perf_counter()
    search_start = time.perf_counter()
    while True:
        now = time.perf_counter()
        if now >= deadline:
            break
        if cfg.max_iterations and IP[K.IP_ITER] >= cfg.max_iterations:
            stop_reason = "max_iterations"
            break
        span = max(deadline - search_start, 1e-9)
        frac = min(1.0, (now - search_start) / span)
        if cfg.max_iterations:
            frac = max(frac, IP[K.IP_ITER] / cfg.max_iterations)
        temperature = t_start * (t_end / t_start) ** frac if t_start > 0 else 0.0
        n_iter = chunk
        if cfg.max_iterations:
            n_iter = int(min(n_iter, cfg.max_iterations - IP[K.IP_ITER]))
        t0 = time.perf_counter()
        K.alns_chunk(inst, cur, cand, best, IP, P, wd, wr, sd, sr, ud, ur,
                     order, n_iter, temperature, stats, pool, buf)
        elapsed = time.perf_counter() - t0
        # adapt the chunk so that time checks happen every ~chunk_seconds
        if elapsed < cfg.chunk_seconds / 2:
            chunk = min(chunk * 2, 1 << 20)
        elif elapsed > cfg.chunk_seconds * 2 and chunk > 1:
            chunk = max(1, chunk // 2)
        remaining = deadline - time.perf_counter()
        per_iter = elapsed / max(n_iter, 1)
        if per_iter > 0:
            chunk = max(1, min(chunk, int(remaining / per_iter / 2) + 1))
        objective = K.objective(best[5], penalty)
        stamp = time.perf_counter()
        if objective < last_best - K.EPS_COST:
            last_best = objective
            time_to_best = stamp - budget_origin
            trace.append(dict(seconds=round(stamp - budget_origin, 4), iteration=int(IP[K.IP_ITER]),
                              best_cost=best_cost(), current_cost=float(cur[5][0]),
                              temperature=temperature, event="improvement"))
            last_trace = stamp
        elif stamp - last_trace > 2.0:
            trace.append(dict(seconds=round(stamp - budget_origin, 4), iteration=int(IP[K.IP_ITER]),
                              best_cost=best_cost(), current_cost=float(cur[5][0]),
                              temperature=temperature, event="heartbeat"))
            last_trace = stamp

    routes = decode_routes(best)
    feasible_state = int(best[5][1]) == 0
    claimed = route_cost(instance, routes) if feasible_state else None
    finish = time.perf_counter()
    trace.append(dict(seconds=round(finish - budget_origin, 4), iteration=int(IP[K.IP_ITER]),
                      best_cost=claimed, current_cost=float(cur[5][0]), event="stop"))
    metadata = dict(
        algorithm="ALNS+VND", version=VERSION, seed=seed, config=cfg.to_dict(),
        jit=JIT_ENABLED, numba_version=_numba_version(), source_sha256=source_fingerprint(),
        stop_reason=stop_reason, iterations=int(IP[K.IP_ITER]),
        construction_seconds=construct_seconds,
        search_seconds=finish - search_start, solver_call_seconds=finish - call_start,
        process_start_known=origin is not None,
        pre_call_seconds=(call_start - origin) if origin is not None else None,
        time_to_best_seconds=time_to_best, deadline_seconds=deadline - budget_origin,
        initial_cost=initial_cost if initial_unassigned == 0 else None, initial_unassigned=initial_unassigned,
        unassigned=int(best[5][1]), routes_used=len(routes), max_routes=R,
        destroy_size=[q_min, q_max], neighbours=int(inst[4].shape[1]),
        final_destroy_weights=dict(zip(DESTROY_OPERATORS, wd.tolist())),
        final_repair_weights=dict(zip(REPAIR_OPERATORS, wr.tolist())),
        stats=dict(iterations=int(stats[K.ST_ITERS]), accepted=int(stats[K.ST_ACCEPT]),
                   improved_current=int(stats[K.ST_IMPROVE_CUR]), new_best=int(stats[K.ST_NEW_BEST]),
                   restarts=int(stats[K.ST_RESTARTS]), incomplete_candidates=int(stats[K.ST_INFEASIBLE_CAND]),
                   vnd_moves=int(stats[K.ST_VND_MOVES])),
        temperature=dict(start=t_start, end=t_end, mean_arc=mean_arc),
    )
    if not feasible_state:
        return SolverResult(None, status="no_solution", trace=trace, metadata=metadata)
    return SolverResult(routes, departure_times=None, status="completed", claimed_cost=claimed,
                        trace=trace, metadata=metadata)


def _numba_version():
    try:
        import numba
        return numba.__version__
    except ImportError:
        return None


def warmup():
    """Compile (or load cached) kernels on a tiny instance."""
    xy = np.array([[0, 0], [1, 0], [2, 0], [0, 2], [3, 3], [1, 1]], float)
    d = np.floor(10 * np.hypot(*(xy[:, None, :] - xy[None, :, :]).transpose(2, 0, 1))) / 10
    inst = CVRPTWInstance("warmup", [0, 1, 1, 1, 1, 1], 3, 4, d, [[0, 100]] * 6, [0, 1, 1, 1, 1, 1])
    return solve(inst, {"max_iterations": 50, "time_reserve": 0.0}, 0, 30.0)
