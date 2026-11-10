"""ALNS + VND correctness tests (solver code taken from main.ipynb).

Every VND move is checked against a brute-force reference: for random feasible
states and every (u, v) pair the expected resulting routes are built in plain
Python, judged by the shared independent validator ``check_cvrptw`` and
compared with what the Numba kernel decides and produces.  Incremental route
data are compared with a from-scratch recomputation after every operation.
"""
from dataclasses import replace
import math
import unittest

import numpy as np

from scripts.notebook_solver import load as load_notebook_solver

# The solver under test is the one written in main.ipynb (built into outputs/alns_build).
ALNS, _ = load_notebook_solver()
ALNSConfig, solve, K = ALNS.ALNSConfig, ALNS.solve, ALNS.kernels
build_instance_data, decode_routes = ALNS.solver.build_instance_data, ALNS.solver.decode_routes
new_solution, route_cost = ALNS.solver.new_solution, ALNS.solver.route_cost
from scripts.benchmark import evaluate_solution, run_solver
from scripts.cvrptw_model import CVRPTWInstance, check_cvrptw, dimacs_tenths, load_cvrptw
from tests.test_model import DATA


def random_instance(n, seed, asymmetric=False, tight=False, K_max=None):
    """Synthetic CVRPTW with DIMACS distances; every customer servable alone."""
    rng = np.random.default_rng(seed)
    xy = np.vstack([[50, 50], rng.integers(0, 101, (n, 2))]).astype(float)
    ticks = dimacs_tenths(xy)
    dist = ticks / 10
    travel = dist.copy()
    if asymmetric:
        travel = dist + rng.integers(0, 30, dist.shape) / 10
        np.fill_diagonal(travel, 0)
        dist = travel.copy()
        ticks = None
    H = 400.0
    service = np.r_[0, rng.integers(0, 11, n)].astype(float)
    centre = rng.uniform(travel[0, 1:], H - travel[1:, 0] - service[1:] - 1)
    width = rng.uniform(5, 40 if tight else 150, n)
    a = np.maximum(travel[0, 1:], centre - width / 2)
    b = np.minimum(H - travel[1:, 0] - service[1:], centre + width / 2)
    windows = np.vstack([[0, H], np.c_[np.floor(a), np.floor(np.maximum(a, b))]])
    demands = np.r_[0, rng.integers(1, 11, n)].astype(float)
    return CVRPTWInstance(f"rand{n}-{seed}", demands, 30.0, K_max or n, dist, windows, service,
                          coordinates=xy, travel_times=travel,
                          distance_tenths=ticks if ticks is not None else None,
                          distance_policy="dimacs_truncate_1_decimal" if ticks is not None else "supplied")


def make_state(instance, seed, cfg=None):
    cfg = cfg or ALNSConfig()
    inst = build_instance_data(instance, cfg)
    N = inst[2].shape[1]
    sol = new_solution(N, min(instance.max_vehicles, N - 1), np.zeros(1, np.int64))
    pool = np.arange(1, N, dtype=np.int64)
    K.seed_rng(seed)
    left = K.repair_blink(inst, sol, pool, N - 1, 0.3, 0)   # random-ish feasible state
    K.refresh_score(sol[0], sol[2], sol[3], sol[5])
    return inst, sol, left


def clone(sol):
    return tuple(a.copy() if i < 6 else a for i, a in enumerate(sol))


def assert_consistent(test, instance, inst, sol):
    """Incremental data == recomputation from scratch, and state is feasible."""
    fresh = clone(sol)
    for r in range(sol[2].shape[1]):
        K.update_route(inst[0], inst[1], inst[2], fresh[0], fresh[1], fresh[2], fresh[3], fresh[6], r)
    for key in (K.NXT, K.PRV, K.RTE, K.POS):
        np.testing.assert_array_equal(fresh[0][key], sol[0][key])
    assigned = sol[0][K.RTE, 1:] >= 0
    np.testing.assert_allclose(fresh[1][:, 1:][:, assigned], sol[1][:, 1:][:, assigned], atol=1e-9)
    np.testing.assert_array_equal(fresh[2][:3], sol[2][:3])
    np.testing.assert_allclose(fresh[3], sol[3], atol=1e-9)
    routes = decode_routes(sol)
    if not np.any(~assigned):
        audit = check_cvrptw(instance, routes, tolerance=1e-7)
        test.assertTrue(audit["feasible"], audit["errors"])
        test.assertAlmostEqual(audit["distance"], K.total_cost(sol[2], sol[3]), places=6)


def plan_cost(instance, routes):
    return sum(float(instance.distances[i, j]) for r in routes for i, j in zip([0] + r, r + [0]))


def plan_feasible(instance, routes):
    if len([r for r in routes if r]) > instance.max_vehicles:
        return False
    a0, H = instance.time_windows[0]
    for r in routes:
        if not r:
            continue
        if instance.demands[r].sum() > instance.capacity + 1e-9:
            return False
        t, prev = a0, 0
        for u in r:
            t = max(t + instance.travel_times[prev, u], instance.time_windows[u, 0])
            if t > instance.time_windows[u, 1] + 1e-9:
                return False
            t += instance.service_durations[u]
            prev = u
        if t + instance.travel_times[prev, 0] > H + 1e-9:
            return False
    return True


def route_lists(sol):
    """Routes by route id (empty lists kept) for reference move construction."""
    I, RI = sol[0], sol[2]
    out = []
    for r in range(RI.shape[1]):
        route, u = [], int(RI[K.FIRST, r])
        while u != 0:
            route.append(u)
            u = int(I[K.NXT, u])
        out.append(route)
    return out


def where(routes, u):
    for r, route in enumerate(routes):
        if u in route:
            return r, route.index(u)
    raise KeyError(u)


# ---------------------------------------------- reference move definitions --
def ref_relocate(routes, u, v, rv):
    ru, pu = where(routes, u)
    new = [list(r) for r in routes]
    if v != 0 and v == u:
        return None
    target = new[rv]
    nxt = target[0] if v == 0 and target else (target[target.index(v) + 1] if v and target.index(v) + 1 < len(target) else 0)
    if v == 0 and not target:
        nxt = 0
    if nxt == u:
        return None
    new[ru].remove(u)
    target = new[rv]
    target.insert(0 if v == 0 else target.index(v) + 1, u)
    return new


def ref_swap(routes, u, v):
    if u == v:
        return None
    new = [list(r) for r in routes]
    ru, pu = where(new, u)
    rv, pv = where(new, v)
    new[ru][pu], new[rv][pv] = v, u
    return new


def ref_two_opt_star(routes, u, v):
    ru, pu = where(routes, u)
    rv, pv = where(routes, v)
    if ru == rv:
        return None
    new = [list(r) for r in routes]
    new[ru] = routes[ru][:pu + 1] + routes[rv][pv:]
    new[rv] = routes[rv][:pv] + routes[ru][pu + 1:]
    return new


def ref_or_opt(routes, u, length, v, reverse):
    ru, pu = where(routes, u)
    string = routes[ru][pu:pu + length]
    if len(string) < length or v in string:
        return None
    rv, pv = where(routes, v)
    route_u = routes[ru]
    pf = route_u[pu - 1] if pu > 0 else 0
    nl = route_u[pu + length] if pu + length < len(route_u) else 0
    if not reverse and v == pf:
        return None
    if reverse and v == nl:
        return None
    new = [list(r) for r in routes]
    for x in string:
        new[ru].remove(x)
    target = new[rv]
    idx = target.index(v)
    if reverse:
        target[idx:idx] = string[::-1]
    else:
        target[idx + 1:idx + 1] = string
    return new


def ref_two_opt(routes, u, v):
    ru, pu = where(routes, u)
    rv, pv = where(routes, v)
    if ru != rv or u == v:
        return None
    i, j = sorted((pu, pv))
    if i + 1 == j:
        return None
    new = [list(r) for r in routes]
    new[ru][i + 1:j + 1] = new[ru][i + 1:j + 1][::-1]
    return new


class MoveReferenceTests(unittest.TestCase):
    """Kernel decision == (reference result feasible and strictly cheaper)."""

    def run_moves(self, instance, seeds=4):
        checked = applied = 0
        for seed in range(seeds):
            inst, sol, left = make_state(instance, seed)
            self.assertEqual(left, 0)
            assert_consistent(self, instance, inst, sol)
            dist, tt, ND, cap, sym = inst[0], inst[1], inst[2], inst[3], inst[7]
            buf = np.zeros(ND.shape[1], np.int64)
            routes = route_lists(sol)
            base = plan_cost(instance, routes)
            n = ND.shape[1] - 1
            cases = []
            for u in range(1, n + 1):
                for v in range(1, n + 1):
                    if u == v:
                        continue
                    rv = where(routes, v)[0]
                    pv = routes[rv].index(v)
                    before_v = routes[rv][pv - 1] if pv > 0 else 0
                    cases.append(("relocate", (u, v, rv), lambda s, u=u, v=v, rv=rv: K.try_relocate(
                        dist, tt, ND, cap, s[0], s[1], s[2], s[3], s[6], u, v, rv, buf), ref_relocate(routes, u, v, rv)))
                    cases.append(("relocate-before", (u, before_v, rv), lambda s, u=u, b=before_v, rv=rv: K.try_relocate(
                        dist, tt, ND, cap, s[0], s[1], s[2], s[3], s[6], u, b, rv, buf), ref_relocate(routes, u, before_v, rv)))
                    cases.append(("swap", (u, v), lambda s, u=u, v=v: K.try_swap(
                        dist, tt, ND, cap, s[0], s[1], s[2], s[3], s[6], u, v, buf), ref_swap(routes, u, v)))
                    cases.append(("2opt*", (u, v), lambda s, u=u, v=v: K.try_two_opt_star(
                        dist, tt, ND, cap, s[0], s[1], s[2], s[3], s[6], u, v), ref_two_opt_star(routes, u, v)))
                    cases.append(("2opt", (u, v), lambda s, u=u, v=v: K.try_two_opt(
                        dist, tt, ND, sym, s[0], s[1], s[2], s[3], s[6], u, v, buf), ref_two_opt(routes, u, v)))
                    for length in (2, 3):
                        for rev in (False, True):
                            cases.append((f"oropt{length}{'r' if rev else ''}", (u, v),
                                          lambda s, u=u, v=v, L=length, rv_=rev: K.try_or_opt(
                                              dist, tt, ND, cap, sym, s[0], s[1], s[2], s[3], s[6], u, L, v, rv_, buf),
                                          ref_or_opt(routes, u, length, v, rev)))
            for name, args, kernel, expected in cases:
                trial = clone(sol)
                moved = kernel(trial)
                if expected is None:
                    self.assertFalse(moved, (name, args))
                    continue
                delta = plan_cost(instance, expected) - base
                should = plan_feasible(instance, expected) and delta < -1e-7
                if abs(delta) < 1e-6:
                    continue  # numerically ambiguous ties are not asserted
                checked += 1
                self.assertEqual(moved, should, (name, args, delta, routes))
                if moved:
                    applied += 1
                    got = [r for r in route_lists(trial) if r]
                    self.assertEqual(sorted(map(tuple, got)), sorted(tuple(r) for r in expected if r), (name, args))
                    assert_consistent(self, instance, inst, trial)
                else:
                    np.testing.assert_array_equal(trial[0], sol[0])
        self.assertGreater(checked, 1000)
        self.assertGreater(applied, 10)

    def test_moves_symmetric_dimacs(self):
        self.run_moves(random_instance(14, 1))

    def test_moves_tight_windows(self):
        self.run_moves(random_instance(14, 2, tight=True))

    def test_moves_asymmetric_travel(self):
        self.run_moves(random_instance(12, 3, asymmetric=True))


class SegmentTests(unittest.TestCase):
    def test_prefix_suffix_feasibility_matches_simulation(self):
        rng = np.random.default_rng(0)
        for seed in range(30):
            instance = random_instance(10, 100 + seed, tight=seed % 2 == 0)
            inst = build_instance_data(instance, ALNSConfig())
            N = inst[2].shape[1]
            sol = new_solution(N, 1, np.zeros(1, np.int64))
            order = rng.permutation(np.arange(1, N))[: rng.integers(1, N)]
            K.set_route(inst[0], inst[1], inst[2], sol[0], sol[1], sol[2], sol[3], sol[6], 0,
                        order.astype(np.int64), len(order))
            last = sol[2][K.LAST, 0]
            first = sol[2][K.FIRST, 0]
            tw_prefix = K.join_tw(inst[1], inst[2], sol[1], last, 0)
            tw_suffix = K.join_tw(inst[1], inst[2], sol[1], 0, first)
            expected = plan_feasible(replace(instance, capacity=1e9), [order.tolist()])
            self.assertEqual(tw_prefix <= K.EPS_TW, expected)
            self.assertEqual(tw_suffix <= K.EPS_TW, expected)
            self.assertEqual(bool(K.seq_feasible(inst[1], inst[2], order.astype(np.int64), len(order))), expected)


class OperatorTests(unittest.TestCase):
    def test_destroy_repair_vnd_keep_state_consistent(self):
        instance = random_instance(40, 7)
        cfg = ALNSConfig()
        inst, sol, left = make_state(instance, 0, cfg)
        self.assertEqual(left, 0)
        N = inst[2].shape[1]
        R = sol[2].shape[1]
        pool = np.zeros(N, np.int64)
        buf = np.zeros(N, np.int64)
        order = np.arange(K.N_NEIGHBOURHOODS, dtype=np.int64)
        for it in range(60):
            K.seed_rng(it)
            dirty = np.zeros(R, np.bool_)
            m, d = 0, it % K.N_DESTROY
            I, RI = sol[0], sol[2]
            if d == K.D_RANDOM:
                m = K.destroy_random(I, RI, pool, m, 6, dirty)
            elif d == K.D_WORST:
                m = K.destroy_worst(inst[0], I, RI, pool, m, 6, dirty, 3.0)
            elif d == K.D_SHAW:
                m = K.destroy_shaw(inst[6], I, RI, pool, m, 6, dirty, 6.0)
            elif d == K.D_STRING:
                m = K.destroy_string(inst[5], I, RI, pool, m, dirty, 10.0, 10, 0.5, 0.01, buf)
            else:
                m = K.destroy_route(I, RI, pool, m, dirty)
            self.assertEqual(len(set(pool[:m].tolist())), m)
            self.assertTrue(np.all(sol[0][K.RTE, pool[:m]] == -1))
            for r in range(R):
                if dirty[r]:
                    K.update_route(inst[0], inst[1], inst[2], sol[0], sol[1], sol[2], sol[3], sol[6], r)
            assert_consistent(self, instance, inst, sol)
            rp = it % K.N_REPAIR
            if rp == K.R_BLINK:
                left = K.repair_blink(inst, sol, pool, m, 0.01, it % 2)
            else:
                left = K.repair_regret(inst, sol, pool, m, rp + 1 if rp else 1, 0.0, it % 2)
            self.assertEqual(left, 0)
            K.refresh_score(sol[0], sol[2], sol[3], sol[5])
            before = sol[5][0]
            K.vnd(inst, sol, order, 30, buf)
            self.assertLessEqual(sol[5][0], before + 1e-9)
            assert_consistent(self, instance, inst, sol)

    def test_vnd_reaches_local_optimum(self):
        instance = random_instance(30, 11)
        inst, sol, _ = make_state(instance, 3)
        buf = np.zeros(inst[2].shape[1], np.int64)
        order = np.arange(K.N_NEIGHBOURHOODS, dtype=np.int64)
        K.vnd(inst, sol, order, 30, buf)
        sol[4][:] = 0  # forget stamps: a fresh full sweep must find nothing
        self.assertEqual(K.vnd(inst, sol, order, 30, buf), 0)


class SolverTests(unittest.TestCase):
    def check_result(self, instance, result):
        self.assertEqual(result.status, "completed")
        audit = check_cvrptw(instance, result.routes)
        self.assertTrue(audit["feasible"], audit["errors"])
        self.assertAlmostEqual(audit["distance"], result.claimed_cost, places=7)
        self.assertEqual(result.claimed_cost, route_cost(instance, result.routes))
        return audit

    def test_small_instances_and_determinism_by_iterations(self):
        instance = random_instance(25, 5)
        cfg = {"max_iterations": 300, "time_reserve": 0.0}
        first = solve(instance, cfg, 7, 60.0)
        second = solve(instance, cfg, 7, 60.0)
        self.check_result(instance, first)
        self.assertEqual(first.routes, second.routes)  # iteration budget => reproducible
        self.assertEqual(first.metadata["stop_reason"], "max_iterations")
        self.assertLessEqual(first.claimed_cost, first.metadata["initial_cost"] + 1e-9)

    def test_asymmetric_and_tight(self):
        for instance in (random_instance(20, 8, asymmetric=True), random_instance(20, 9, tight=True)):
            self.check_result(instance, solve(instance, {"max_iterations": 200}, 1, 60.0))

    def test_single_customer_and_fleet_limit(self):
        one = random_instance(1, 3)
        self.check_result(one, solve(one, {"max_iterations": 5}, 0, 10.0))
        # three demands of 6 with Q=10: impossible with K=2, feasible with K=3
        xy = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], float)
        ticks = dimacs_tenths(xy)
        base = CVRPTWInstance("packing", [0, 6, 6, 6], 10.0, 2, ticks / 10, [[0, 100]] * 4, [0, 0, 0, 0],
                              coordinates=xy, distance_tenths=ticks, distance_policy="dimacs_truncate_1_decimal")
        impossible = solve(base, {"max_iterations": 50}, 0, 10.0)
        self.assertEqual(impossible.status, "no_solution")
        self.assertIsNone(impossible.routes)
        self.assertGreater(impossible.metadata["unassigned"], 0)
        self.check_result(replace(base, max_vehicles=3), solve(replace(base, max_vehicles=3), {"max_iterations": 50}, 0, 10.0))

    def test_c101_reaches_reference_quickly(self):
        instance = load_cvrptw(DATA / "Solomon/C101.vrp")
        result = solve(instance, {"time_reserve": 0.0}, 0, 5.0)
        audit = self.check_result(instance, result)
        self.assertLessEqual(audit["distance"], 827.3 * 1.01)
        self.assertLessEqual(len(audit["active_routes"]), instance.max_vehicles)

    def test_time_limit_respected_in_isolated_worker(self):
        instance = load_cvrptw(DATA / "Solomon/R101.vrp")
        current, _ = load_notebook_solver()  # workers pickle solve by reference to the live module
        result, timing = run_solver(current.solve, instance, {"clock": "process"}, 3, 6.0)
        self.assertTrue(timing["budget_respected"], timing)
        self.assertIsNone(timing["error"])
        reference = dict(status="verified", recomputed_cost=1637.7)
        metrics = evaluate_solution(instance, result, reference)
        self.assertTrue(metrics["feasible"], metrics["errors"])
        self.assertTrue(metrics["cost_agrees"])
        self.assertTrue(math.isfinite(metrics["gap_percent"]))

    def test_config_validation(self):
        for bad in ({"unknown": 1}, {"destroy_min": 50, "destroy_max": 10}, {"time_fraction": 1.5},
                    {"destroy_weights": [0, 0, 0, 0, 0]}, {"neighbourhoods": ["relocate", "bogus"]},
                    {"temp_start": 0.01, "temp_end": 1.0}, {"n_neighbours": 0}, {"clock": "wall"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ALNSConfig.from_dict(bad)
        self.assertEqual(ALNSConfig.from_dict(ALNSConfig().to_dict()), ALNSConfig())


if __name__ == "__main__":
    unittest.main()
