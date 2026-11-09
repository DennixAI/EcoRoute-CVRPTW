# EcoRoute — Benchmarking and Experimental Evaluation Protocol

> **Purpose:** execution contract for coding agents, researchers, and the final CESI report.  
> **Selected datasets:** Solomon (100 customers) and Gehring–Homberger (200–1,000 customers), as specified in [`dataset.md`](dataset.md).  
> **Target algorithm:** capacitated vehicle routing with time windows and a separate time-dependent traffic extension (**TD-CVRPTW**).  
> **Status:** specification, **not** an assertion that the runner, datasets, algorithms, or results already exist.  
> **Read alongside:** [`dataset.md`](dataset.md), [`sources.md`](sources.md), [`context.md`](context.md), and [`README.md`](README.md). Older documents may still reflect the historical CVRP-only scope.

## 1. What CESI requires — and what we will demonstrate

The original assignment, preserved verbatim in [`sources.md`](sources.md), requires:

- A Python heuristic/metaheuristic solver, not merely a mathematical model or a call to a reference solution.
- **At least 20 different problem instances**, representing varied sizes, customer distributions, and constraints. Repeated random seeds on one instance do **not** count as additional instances.
- The **`vrplib` Python library to load reference instances**, comparison with best-known solutions, and a reported percentage gap:

  \[\mathrm{gap}(\%)=100\frac{\mathrm{our\ cost}-\mathrm{reference\ cost}}{\mathrm{reference\ cost}}.\]

- Quality, elapsed computation time, statistical analysis, visualizations, sensitivity, limitations, and justified improvements; a reproducible demonstration in the final notebook/presentation.
- Level **B**: CVRP with one homogeneous truck capacity per instance. Level **A**: CVRPTW with hard delivery windows. The motivating description additionally calls for predicted, time-dependent traffic and tour-duration optimization.

**Our evaluation has two primary tracks:** **S — native static VRPTW**, where published benchmarks are directly comparable, and **T — traffic-augmented TD-CVRPTW**, where they generally are not. An optional **C — classical CVRP** regression track is not a substitute for the advanced tests.

The assignment warns that gaps above approximately **7–10% can cap the grade at B**. This is a grading warning, **not** proof that a given benchmark score guarantees a grade. Do not fabricate results or hide failures.

## 2. Choose the benchmark protocol *before* running anything

| Track | Input | Primary objective and evaluator | Valid comparison |
| --- | --- | --- | --- |
| **S-A — CVRPLIB VRPTW (recommended primary static track)** | Unmodified Solomon/Homberger files | **Minimize total distance**, at most `K` trucks; each Euclidean arc distance **truncated to 1 decimal**; total distance reported to 1 decimal | **CVRPLIB** VRPTW `UB`/`Opt`, under exactly those rules |
| **S-B — SINTEF VRPTW (optional, separately reported)** | Same underlying families | **Lexicographic:** minimize trucks first, then total **double-precision Euclidean** distance; total displayed to 2 decimals | **SINTEF** pair `(vehicles, distance)` only |
| **T — TD-CVRPTW (our advanced traffic track)** | Base VRPTW files + a separately versioned traffic scenario | **Explicit time-based objective** defined in the run configuration, with full time-dependent route schedules | Only other feasible methods/valid bounds on **the identical traffic instance** |

**Never merge S-A and S-B into a single gap leaderboard.** Their objectives and edge costs differ. **Never use a static optimum/BKS for a traffic-modified instance.**

**Example:** CVRPLIB lists Solomon `C101` at **827.3** under S-A (marked optimal), whereas SINTEF lists **10 trucks / 828.94 distance** under S-B. Both can be correct under their respective conventions. A discrepancy is not evidence that our algorithm beat the optimum.

For the project, implement **S-A first**, because its single distance objective aligns naturally with the gap formula in the assignment. Include S-B only if we explicitly want to study the alternative fleet-first objective and maintain its separate evaluator. Track T is essential for the additional traffic-aware project goal.

## 3. Source of datasets, references, and reproducibility

1. Obtain **original, unchanged** Solomon 100-customer files and Gehring–Homberger 200/400/600/800/1,000-customer files. Use the [CVRPLIB VRPTW catalog](https://galgos.inf.puc-rio.br/cvrplib/index.php/en/vrptw/instances) or [SINTEF Solomon](https://www.sintef.no/projectweb/top/vrptw/100-customers/) / [SINTEF Homberger](https://www.sintef.no/projectweb/top/vrptw/homberger-benchmark/) download pages. Keep the original filename and archive.
2. Read the [official `vrplib` README](https://github.com/PyVRP/VRPLIB): `vrplib` **parses and writes files; it is not an optimizer** and does not itself guarantee the required dataset archive or correct solution feasibility.
3. Create a `data/manifests/instances.csv` with at least `instance_id, family, class, n_customers, original_path, source_url, sha256, split, reference_protocol, reference_source, reference_cost, reference_vehicles, proven_optimal, reference_checked_at`. Record unavailable reference values as **null**, not zero.
4. Download/record **published reference routes** when available; some catalog entries provide only a value. Never interpret the published route as one discovered by our solver.
5. Preserve `data/raw/` byte-for-byte. Store conversions, caches, test manifests, traffic overlays, and results in **separate versioned paths**. Record download date and applicable source/usage terms.

**Proposed layout** (create these directories when implementing; they are not claimed to exist):

```text
project-root/
  dataset.md                 # dataset specification and instance conventions
  benchmarks.md              # this execution and reporting contract
  benchmarks/vrptw/          # downloaded .vrp inputs and .sol reference solutions
  data/manifests/{instances.csv,split.csv,references.csv}
  data/derived/traffic/      # derived overlays only, never overwrite raw data
  configs/benchmarks/        # frozen, versioned experiment configurations
  src/                       # solver and independent evaluation modules
  tests/                     # parser, schedule, objective, traffic tests
  results/<experiment_id>/   # immutable result files and provenance
```

## 4. Load and normalize a benchmark instance

Install the minimal parsing dependencies in a clean environment (pin exact versions in the eventual lockfile):

```bash
python -m pip install vrplib numpy pandas matplotlib
```

**Working parser example** (assuming the official file has already been downloaded):

```python
from pathlib import Path
import numpy as np
import vrplib

path = Path("data/raw/solomon/C101.txt")
raw = vrplib.read_instance(str(path), instance_format="solomon")

xy = np.asarray(raw["node_coord"], dtype=float)
q = np.asarray(raw["demand"], dtype=float)
tw = np.asarray(raw["time_window"], dtype=float)
service = np.asarray(raw["service_time"], dtype=float)
K, Q = int(raw["vehicles"]), float(raw["capacity"])

assert len(xy) == len(q) == len(tw) == len(service)
assert xy.shape[1] == 2 and tw.shape[1] == 2
assert K > 0 and Q > 0 and np.all(q >= 0)
assert np.all(tw[:, 0] <= tw[:, 1])
print(path.stem, "customers:", len(q) - 1, "vehicles:", K, "capacity:", Q)
```

The same loader works for Homberger's Solomon-format `.txt` instances. Use an internal canonical instance object; **do not** hard-code `K=25`, `Q=200`, customer count, node coordinates, or the time horizon. Standard input uses depot node `0` and customers `1..n`; verify and record any remapping.

`vrplib` can calculate `edge_weight`, but **its default Euclidean matrix does not necessarily match the selected leaderboard's truncation policy**. The benchmark evaluator—not the parser's default—is authoritative. For large instances, avoid constructing multiple redundant dense matrices.

## 5. Build an **independent** route and cost evaluator

**This is mandatory before writing benchmark claims.** The evaluator must accept an instance plus explicit routes and departure times, without trusting flags or objective values returned by the optimizer. Implement a single shared feasibility core with a protocol-specific distance/travel-time provider.

For a route `r = [i1, ..., ip]`, independently verify:

1. **Coverage:** every customer occurs **exactly once** across all routes; no depot mistakenly treated as a customer; no missing, duplicated, or unknown customer IDs.
2. **Fleet:** number of nonempty routes `<= K`; each truck uses the same per-instance capacity `Q`.
3. **Load:** `sum(q[i] for i in r) <= Q`; demands cannot be split between trucks.
4. **Chronology:** for each arc `(i, j)`, `arrival_j = departure_i + travel_time(i, j, departure_i)`; `start_j = max(arrival_j, ready_j)`; `start_j <= due_j`; `departure_j = start_j + service_j`.
5. **Depot:** trucks leave within the permitted depot window and return by the depot deadline; record earliest departure, route return, driving time, waiting and service.
6. **Objective:** include every depot-to-first-customer, between-customer, and last-customer-to-depot arc. Use the **selected protocol's edge precision**; never substitute a rounded display value for evaluation.
7. **Numeric policy:** use a small, documented tolerance for floating-point boundary tests; never change published raw input or move a delivery window to make an invalid route pass.

**Static S-A costs:** `distance(i,j) = floor(10 * hypot(dx,dy)) / 10` under the official CVRPLIB evaluation convention, with any necessary floating-point boundary behavior verified against official reference routes/evaluators. Native static travel time equals this distance. The reported total uses the catalog's prescribed 1-decimal output convention.

**Static S-B costs:** `distance(i,j) = hypot(dx,dy)` in double precision; keep full precision throughout feasibility and summation; only **display** total to 2 decimals. Rank solutions by `(used_vehicles, total_distance)`, not solely by distance.

**Time windows:** `DUE DATE` conventionally means latest **service start**, not latest service completion. Early arrivals can wait. An arrival too late for a valid service start is infeasible. Include the depot's return deadline.

**Reference gate:** before any batch experiment, take at least one *fully specified published reference route* and independently reproduce its feasibility and cost **under the chosen source's convention**. Check Solomon `C101` and also one `R` or `RC` and one Homberger example, where compatible detailed routes exist. If reproduction fails, **stop and fix parsing, distance precision, route-index interpretation, or time evaluation before reporting gaps**. A table-only reference cost is not a substitute for validating a route.

Test the validator on intentionally defective solutions: duplicate/missing stops, overloaded truck, more than `K` routes, premature service, missed opening/closing time, missed depot return, wrong depot ID, invalid demand, nonzero service time, exact window boundary, and traffic interval crossing. Separate `infeasible`, `timeout`, and `program_error` outcomes.

## 6. Correct gaps, comparisons, and metric definitions

For S-A only, with a **positive, comparable** published cost `B`:

```python
gap_percent = 100.0 * (our_valid_distance - reference_distance) / reference_distance
```

- If the reference is **proven optimal**, label `gap_to_optimum_%`.
- If the reference is merely best known, label `gap_to_BKS_%`; negative values may indicate an improvement, but require independent verification.
- If our solution is **infeasible**, or the reference objective/rounding/source differs, the gap is **undefined** (`null`), never `0`, never an invented penalty.
- For S-B, compare **vehicle count first**. Compare scalar distance gaps **only for matching fleet counts**, and label them as distance differences within that fleet-count class—not proof of an optimum unless certified.
- For T, report a **time-objective improvement over a valid TD baseline on identical traffic**, not a gap to Solomon/Homberger static BKS. A true TD optimality gap requires a verified time-dependent optimum/bound under precisely matching assumptions.

**Every run must report:** feasibility, customers served, vehicles used, total distance, sum of driving time, sum of waiting time, sum of service time, sum of route elapsed durations, maximum route duration, chosen primary objective value, solver wall-clock seconds, time-to-first-feasible, and reason for failure/timeout. For T, also record road/traffic policy, congestion scenario, scenario seed, and vehicle departure choices.

Keep **solver runtime** separate from parsing, instance conversion, reference loading, figure generation, and independent post-validation; optionally report total end-to-end time too. Time using a monotonic clock (for example `time.perf_counter()`), and record CPU model, RAM, core/thread count, Python/dependency versions, OS, code commit, solver parameters, and whether runs execute in parallel. If memory is measured, state the measurement method and whether peak memory includes the subprocess.

## 7. Freeze a real test set: **24 distinct instances** (recommended)

Choose filenames **after obtaining the source archives**; freeze a manifest before final tuning. Select independently of the algorithm's performance:

| Final static test stratum | Sampling rule | Different instances |
| --- | --- | ---: |
| Solomon, 100 customers | One previously unseen file per class `C1`, `C2`, `R1`, `R2`, `RC1`, `RC2` | **6** |
| Homberger, 200 customers | One previously unseen file per class | **6** |
| Homberger, 600 customers | One previously unseen file per class | **6** |
| Homberger, 1,000 customers | One previously unseen file per class | **6** |
| **Total** | **24 distinct base instance IDs** | **24** |

Add 400- and 800-customer Homberger instances for a stronger scalability curve if time and hardware permit. The **official minimum is 20 distinct instances**, not 24; 24 is **our proposed robust protocol**. Keep development/validation files disjoint from this final set. A minimum of 6–10 additional Solomon development instances from multiple classes is reasonable; reserve separate validation instances for algorithm selection.

**Do not look at final-instance scores to choose neighborhoods, parameter values, model changes, or the preferred metaheuristic.** If final data influence tuning, relabel them development data and select fresh untouched test cases. Use deterministic manifest selection with recorded seed and hashes; explicitly check no same base file appears in two splits.

Each finalist instance should be evaluated under **at least 5 fixed, predeclared random seeds when resources allow** (especially important for stochastic ALNS/ILS). Record the number of repetitions and all failures; repetitions add statistical evidence but **do not increase the distinct-instance count**.

## 8. How the benchmark runner should execute

### A. One-time preparation

1. Pin Python, `vrplib`, dependencies, hardware, source URLs and original data hashes; download Solomon/Homberger archives.
2. Create immutable `instances.csv`, `references.csv`, and `split.csv`; choose S-A as the default comparison protocol.
3. Implement parser/normalizer and **independent** evaluator. Pass malformed-route tests and reproduce published route costs (Section 5).
4. Implement a trivial but fully valid construction baseline; validate its routes independently. Strong external solvers may be used as **attributed comparator baselines** only if their implemented constraints and objectives truly match the run; they must never be misrepresented as our algorithm.
5. Compare candidate solver variants (e.g. ALNS vs ILS + local search) on development/validation instances under the **same per-instance budget**. Freeze the chosen algorithm and hyperparameters before opening the final test split.

### B. Execute a static run

For each instance × algorithm × seed:

1. Load and validate the original file with `vrplib`.
2. Construct the **protocol-specific static travel-time/cost evaluator**.
3. Start a monotonic solver timer. Run the algorithm with `K`, `Q`, windows, service times, seed, and a fixed time budget read from configuration.
4. Persist the best feasible route sequence, detailed schedule, convergence trace (if available), elapsed time, and completion status. Preserve results even when no feasible route was found.
5. Run the **independent evaluator** on the saved route, recomputing cost and constraints. A failing result is **infeasible**, regardless of the optimizer's claim.
6. Compute a gap **only if** the validated solution and published reference follow the same objective and evaluator policy.
7. Write an immutable JSON result and append a summary CSV row; also preserve raw exceptions, error messages and the chosen seed.

### C. Execute a traffic-aware run

1. Select a **frozen base Solomon/Homberger instance** and load its **separate, immutable traffic overlay** (`traffic_scenario_id`, model version, time origin/unit, departure policy, parameters, seed, SHA-256).
2. Validate the time-dependent travel provider, especially FIFO/arrival-time monotonicity and journeys spanning multiple traffic slots. **Do not assume benchmark XY coordinates are real GPS roads.**
3. Declare the **primary time objective** explicitly; a recommended candidate is `sum(return_time_k - departure_time_k)` over active trucks, including waiting/service in elapsed duration. Confirm this modeling choice with the tutor if needed; do not silently substitute makespan or static distance.
4. Run **all compared algorithms on the same base instance, traffic overlay, fleet, budget and objective**; independently recompute the entire schedule after every proposed route move in the checker.
5. Compare against a **feasible traffic-aware baseline** (for example, a repaired static route or simple TD insertion heuristic), not against the original static BKS. If the unmodified static route is infeasible under traffic, report that fact before attempting any repair.
6. Report travel-time improvement, delivery-window feasibility, waiting, route changes, number of vehicles, route elapsed times, speed/traffic sensitivity, runtime, and failures. Label synthetic congestion as synthetic—not measured congestion.

**Traffic feasibility warning:** adding congestion can make some otherwise feasible static cases infeasible with the original time windows and vehicle count. Do **not** quietly relax deadlines, extend the fleet, or drop customers; mark the scenario infeasible/unresolved or explicitly record a modified problem as a *different* experimental case.

### D. Proposed CLI contract (to implement, **not existing commands**)

```bash
# AFTER implementing the benchmark modules and configuration files:
python -m ecoroute.benchmarks prepare --config configs/benchmarks/static_cvrplib.yaml
python -m ecoroute.benchmarks verify  --config configs/benchmarks/static_cvrplib.yaml
python -m ecoroute.benchmarks run     --config configs/benchmarks/static_cvrplib.yaml --split test
python -m ecoroute.benchmarks report  --results results/<experiment_id>/

# Traffic-aware experiments: separate evaluator, objective and output directory.
python -m ecoroute.benchmarks run --config configs/benchmarks/traffic_td_cvrptw.yaml --split test
```

These commands are a **proposed interface**, not verified runnable commands in the current repository. Coding agents may choose equivalent names, but must retain the four stages: **prepare → verify → run → report**, a dry-run/`--help` mode, and fail-fast validation.

The runner should accept a machine-readable config with at least: `protocol`, `dataset_manifest`, `reference_manifest`, `split_manifest`, `algorithms`, `seeds`, `time_budget_seconds_by_size`, `maximum_parallel_jobs`, `distance_policy`, `objective`, `traffic_overlay_manifest_or_null`, `output_directory`, and `error_policy`. Record the full resolved config in the result directory.

## 9. Budgets, repetition, and statistical analysis

- Pick fixed compute budgets appropriate to available hardware and **freeze them before final testing**. Illustrative, *not CESI-mandated*: 30 s for 100-customer tests, 90 s for 200–400, and 180 s for 600–1,000. Within a given instance all compared methods receive the **same budget, CPU/thread allocation, and objective**. Report if different classes receive different budgets.
- Run multiple seeds, preferably **5 or more per stochastic algorithm/instance**, or explicitly document a reduced count and why. Keep baseline algorithms under fair, documented budgets.
- Compute **per-instance** best/mean/median/std, first-feasible time, success rate, timeouts, and valid reference gaps. Then summarize **macro-averages across instances** (equal instance weights) by C/R/RC, 1/2, size, and optionally traffic severity.
- Report feasibility **before** optimization quality. Do not average gaps only across successes without **also** reporting the number and identity of failures. Keep best-versus-mean results distinct; do not report a lucky best seed as typical performance.
- Make plots: per-instance gap; gap by class and size; runtime vs customer count; memory vs customer count; distribution of seed outcomes; convergence vs time; vehicles used; waiting and lateness (must be zero for feasible hard-window cases); and before/after congestion route maps and schedules.
- Explain **why** variants differ: customer geography, window tightness, capacity pressure, traffic severity, available runtime, and construction/repair behavior. Note that classes 1/2 also differ in capacities and time horizon, so class comparisons alone do not isolate one cause.
- Report performance limitations (including failure cases), threats to validity, and concrete next improvements. Statistical confidence intervals/bootstrap estimates are useful when data permit; never claim statistical significance without a suitable test.

## 10. Files required for every experiment and report

Under `results/<experiment_id>/` preserve:

```text
config.resolved.yaml           # actual run parameters and objective
manifest.snapshot.csv          # exact files, hashes, split and references
results.csv                    # one row per instance / solver / seed
runs/<run_id>.json             # routes, schedules, cost breakdown, violations
runs/<run_id>.log              # solver log, exceptions and timings
summary_by_instance.csv        # quality + runtime + feasibility statistics
figures/                       # reproducible graphs/plots
report.md                      # interpretation, assumptions, caveats
```

**Minimum row fields:** `run_id, timestamp, code_commit, instance_id, family, n, class, sha256, split, protocol, distance_policy, objective_name, traffic_scenario_id, solver, parameters_hash, seed, K, Q, wall_time_s, solver_time_s, peak_memory_mb_or_null, feasible, customers_served, vehicles_used, distance, driving_time, waiting_time, service_time, sum_route_duration, max_route_duration, objective_value, reference_value_or_null, reference_type, valid_gap_percent_or_null, status, violation_summary`.

`status` should distinguish `feasible`, `no_feasible_solution`, `time_limit_without_solution`, `error`, and `invalid_output`; an expired time budget **with** a feasible incumbent is a successful feasible outcome *and* a time-limit termination. Keep feasibility and termination reason as **separate fields** if the implementation supports it.

The final notebook must include the experimental design, a transparent results table with **>=20 distinct evaluated base instances**, benchmark conventions and gaps, runtime/scaling plots, statistics, failure cases, traffic experiments, and an English explanation of the algorithm and its limitations. **Figures/animations are not proof of feasibility or optimality.**

## 11. Release gates for agents

Do not call the benchmarking deliverable complete until all of the following hold:

- [ ] Original CESI scope and the latest advanced project choice are distinguished; **at least 20 different instances** are evaluated and counted correctly.
- [ ] Unmodified Solomon and Homberger archives and their SHA-256 hashes are recorded; split is frozen; every needed `K`, `Q`, window, service time and coordinate is loaded from data.
- [ ] `vrplib.read_instance(..., instance_format="solomon")` is used for the relevant benchmark-format files.
- [ ] Separate, independent route validation passes both negative tests and available trusted reference routes.
- [ ] Primary S-A objective, arc truncation and reference convention are exactly reproducible; S-B (if used) is separate; **traffic runs never cite static gaps as TD gaps**.
- [ ] Missing routes, duplicate customers, overloads, late service, depot lateness and excessive vehicles always cause independent validation failure.
- [ ] At least one baseline and our solver are measured under fair matched budgets; raw routes, failures, seeds and resources are retained.
- [ ] Traffic scenarios are versioned, independently feasible-checked and benchmarked against valid TD comparators; no unapproved changes to windows, capacities or fleet.
- [ ] Statistics distinguish best/typical outcomes, success rates and timeouts; conclusions interpret patterns rather than merely present figures.
- [ ] Results can be reproduced from exact dataset hashes, code commit, dependency versions, configuration, machine metadata and random seeds.

## 12. Authoritative sources

1. **[CESI original assignment](https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html)** — 20 distinct instances, `vrplib`, gap, algorithm, runtime and experimental analysis; original transcript is in [`sources.md`](sources.md).
2. **[PyVRP/VRPLIB GitHub](https://github.com/PyVRP/VRPLIB)** — `pip install vrplib`, Solomon loader, parsed dictionary, route/solution format, and caveats about distance precision; **parser, not optimizer**.
3. **[CVRPLIB VRPTW problem conventions](https://galgos.inf.puc-rio.br/cvrplib/index.php/en/vrptw)** and **[instance catalog](https://galgos.inf.puc-rio.br/cvrplib/index.php/en/vrptw/instances)** — static distance-only objective, truncation to one decimal, at-most-`K` fleet, published bounds and optimality flags.
4. **[SINTEF Solomon benchmark](https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/)** and **[Solomon 100 results](https://www.sintef.no/projectweb/top/vrptw/100-customers/)** — hierarchical `(vehicles, distance)` objective, double precision, 2-decimal display, reference route availability.
5. **[SINTEF Homberger benchmark](https://www.sintef.no/projectweb/top/vrptw/homberger-benchmark/)** and **[format and feasibility semantics](https://www.sintef.no/projectweb/top/vrptw/documentation2/)** — same hierarchical standard; `K` maximum; due date = latest service start; depot `0`.
6. **[`dataset.md`](dataset.md)** — selected family inventory, data schema, geographic distributions, raw acquisition and optional external TD datasets.

**Agent priority:** *reproduce a trusted reference correctly → obtain feasible solutions → compare under the same objective and budgets → analyze statistically → only then add traffic, without contaminating static benchmark results.*
