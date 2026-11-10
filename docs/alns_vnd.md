# Algorithm 1 — ALNS + VND for static CVRPTW

Branch `algo/alns-vnd` (worktree `claude/cvrptw-alns-vnd-4fa707`). Code: [`algorithms/alns_vnd/`](../algorithms/alns_vnd/), experiment CLI: [`scripts/run_alns.py`](../scripts/run_alns.py), tests: [`tests/test_alns_vnd.py`](../tests/test_alns_vnd.py).

The solver implements the `scripts.benchmark.Solver` protocol: `solve(instance, config, seed, time_limit) -> SolverResult`. It receives only the `CVRPTWInstance` (never `.sol` routes or costs), returns customer-only routes in internal indices 1..n, and every result is re-validated and re-scored by the shared independent evaluator (`check_cvrptw`, DIMACS integer tenths).

## 1. Search state and feasibility

* **Representation.** Each route is a doubly linked list of customers (depot = sentinel 0). At most `R = min(K, n)` route slots exist, so the fleet limit holds by construction; unused slots are empty routes (no cost).
* **Always feasible states.** Every accepted state satisfies capacity, customer service-start windows and the depot window. A customer that no repair can place stays *unassigned* and is charged a large penalty; such a state is never returned (`status="no_solution"`).
* **O(1) time-window checks.** Every route stores, at each customer, the prefix segment (depot → u) and the suffix segment (u → depot) of the time-window segment algebra of Vidal et al. (2013): `(D, TW, E, L)` = minimum duration, time warp, earliest/latest start. Concatenation is O(1), a sequence is feasible iff its time warp is 0, and the depot segment `[a0, H]` lets the departure time float inside the depot window. Inserting a customer, removing a string, exchanging tails between two routes or moving a (possibly reversed) string of up to 3 customers into another route is therefore checked in constant time. Intra-route moves are re-verified exactly with an O(route length) earliest-schedule pass.
* **Numerics.** Distances and travel times are the instance matrices (DIMACS truncated tenths for the benchmarks). Time warp must be ≤ 1e-9 (the validator allows 1e-7), improvements must exceed 1e-7, and the reported cost is recomputed from the integer-tenths cache.

## 2. ALNS (Ropke & Pisinger 2006; Pisinger & Ropke 2007)

Each iteration copies the current solution, removes `q ∈ [q_min, q_max]` customers with an adaptively selected *destroy* operator, reinserts them with an adaptively selected *repair* operator, optimises the result with the VND (Section 3) and applies simulated-annealing acceptance.

| Destroy | Description |
| --- | --- |
| random | q uniformly random customers |
| worst | rank customers by distance saving, pick rank ⌊y^p·|L|⌋ (p = 3) |
| Shaw | relatedness = 9·distance + 3·window difference + 2·demand difference (normalised), rank ⌊y^p·|L|⌋ (p = 6) from precomputed relatedness lists |
| string (SISR) | Christiaens & Vanden Berghe (2020): remove strings (optionally split around a preserved substring) from the routes nearest to a random seed customer, average ~c̄ = 10 customers |
| route | remove one whole random route (drives route-count reduction) |

| Repair | Description |
| --- | --- |
| greedy | parallel cheapest insertion (regret-1) |
| regret-2 / regret-3 | insert the customer with the largest Σ_{h=2..k}(c_h − c_1) first |
| blink | SISR greedy insertion in a random order rule (random / demand / far / close / window width), skipping each position with probability 0.01 |

Insertion costs are cached per (customer, route) and only the modified route is recomputed after an insertion. Candidate routes for a customer are the routes of its granular neighbours plus one empty route; if none admits it, every route is scanned. Within a route, scanning stops once the customer can no longer be reached in time (earliest service starts grow along a route).

**Adaptive weights:** scores 33 / 9 / 13 for a new global best / an improvement of the current solution / an accepted worse solution, reaction factor 0.1, segments of 100 iterations.

**Acceptance:** simulated annealing with temperature relative to the mean arc length of the initial solution, cooled exponentially with the elapsed fraction of the time budget (or iteration budget). Sideways moves are accepted. An optional restart from the best solution is available (`restart_after`).

## 3. VND

Granular neighbourhoods (Toth & Vigo 2003) over the `G` closest customers in the time-window-aware proximity of Vidal et al. (2013): distance + 0.2·forced waiting + 1.0·lateness, symmetrised.

| Neighbourhood | Move (creates arc u–v) |
| --- | --- |
| relocate | u after v or before v (inter and intra), or u alone into an empty route |
| swap | exchange u and v |
| 2-opt* | tail exchange between two routes, both orientations |
| or-opt | strings of 2–3 customers starting at u, inserted after v or reversed before v |
| 2-opt | intra-route reversal between u and v |

Each neighbourhood is swept with first improvement; after a sweep that improves, the descent restarts at the first neighbourhood, otherwise it moves to the next; it ends at a local optimum of all five. Per-route modification stamps skip (u, v) pairs whose two routes did not change since u was last examined in that neighbourhood, so after a destroy/repair only the affected region is re-examined.

## 4. Implementation and performance

The kernels are plain Python in the Numba-compatible subset, JIT-compiled with Numba 0.60 (BSD licence; disclosed dependency, `algorithms/alns_vnd/requirements.txt`). Without Numba (or with `ECOROUTE_DISABLE_JIT=1`) the same code runs as ordinary Python. Compiled code is cached on disk; the campaign CLI warms the cache before any timed attempt.

A profiling finding shaped the code: handing tuples of arrays to a non-inlined Numba function costs ~100 ns per call (reference counting), whereas passing the arrays individually is ~1 ns. Only per-iteration entry points accept tuples; all hot functions take arrays. This made a full VND sweep ~10× faster (5–60 ns per (u, v) pair and neighbourhood).

## 5. Configuration

All settings are fields of `ALNSConfig` (`algorithms/alns_vnd/config.py`); unknown keys are rejected. The campaign CLI records the complete resolved configuration with every attempt.

## 6. Experimental protocol and results

See [Section 7 of the handbooks](../CLAUDE.md) for the mandatory workflow and [`results/alns-vnd/`](../results/alns-vnd/) for campaigns. Results are summarised in [`results/alns-vnd/README.md`](../results/alns-vnd/README.md).

Frozen configuration (tuned on the development split only): SA temperature 1.5 → 0.02 × mean arc length, 20 VND neighbours, 40 repair-candidate neighbours, q ∈ [5, min(40, 0.2n)], destroy weights random/worst/Shaw/string/route = 1/0/1/1/0.5, all four repair operators.

Held-out test `test-001` (36 instances × 10 seeds, max(10, 0.3·n) s): **360/360 feasible, mean gap 0.654 %, P90 1.448 %, worst run 2.364 %, no run above 7 %**; by size 0.26 % (100) → 1.20 % (1000).

## References

* Christiaens, J., & Vanden Berghe, G. (2020). Slack induction by string removals for vehicle routing problems. *Transportation Science*, 54(2), 417–433.
* Pisinger, D., & Ropke, S. (2007). A general heuristic for vehicle routing problems. *Computers & Operations Research*, 34(8), 2403–2435.
* Ropke, S., & Pisinger, D. (2006). An adaptive large neighborhood search heuristic for the pickup and delivery problem with time windows. *Transportation Science*, 40(4), 455–472.
* Shaw, P. (1998). Using constraint programming and local search methods to solve vehicle routing problems. *CP-98*, LNCS 1520, 417–431.
* Toth, P., & Vigo, D. (2003). The granular tabu search and its application to the vehicle-routing problem. *INFORMS Journal on Computing*, 15(4), 333–346.
* Vidal, T., Crainic, T. G., Gendreau, M., & Prins, C. (2013). A hybrid genetic algorithm with adaptive diversity management for a large class of vehicle routing problems with time-windows. *Computers & Operations Research*, 40(1), 475–489.
* Hansen, P., & Mladenović, N. (2001). Variable neighborhood search: Principles and applications. *European Journal of Operational Research*, 130(3), 449–467.
