# EcoRoute — static CVRPTW solved with ALNS + VND

EcoRoute is a CESI (CesiCDP) project: plan delivery tours for a fleet of identical trucks so that every customer is served inside its time window, no truck is overloaded, and the **total distance driven is as small as possible**. It contains a complete mathematical model, an independent validator, a metaheuristic solver (**ALNS + VND**) written in [`main.ipynb`](main.ipynb), and a reproducible benchmark on the 356 Solomon and Gehring–Homberger instances.

> Project rules, scope decisions and the full benchmarking protocol live in the identical handbooks [AGENTS.md](AGENTS.md) / [CLAUDE.md](CLAUDE.md). Algorithm design notes: [docs/alns_vnd.md](docs/alns_vnd.md). All experiment results: [results/alns-vnd/README.md](results/alns-vnd/README.md).

---

## 1. Problem context

The CESI brief (ADEME mobility call) asks for a delivery tour on a road network that minimises duration under forecast traffic, for large instances, with *k* identical trucks; the advanced level adds delivery time windows (CVRPTW). Gaps above roughly **7–10 %** to reference solutions can cap the grade at B.

**Selected scope** (an explicit team decision, to be acknowledged by the tutor):

| Included | Excluded |
| --- | --- |
| One depot; every customer served exactly once (no split deliveries) | Time-dependent traffic, road networks, MAMUT data |
| At most **K** identical trucks of capacity **Q** (fewer may be used) | Emissions objective, multiple depots, truck-specific departure windows |
| Hard **service-start** windows $[a_i,b_i]$; early arrival waits; service may finish after $b_i$ | Forcing exactly K trucks or minimising the fleet first |
| Service durations; common depot window $[a_0,H]$ for departure and return | Instances above 1,000 customers (scalability beyond that is unproven) |
| Objective: **total distance** (duration, waiting, route count and load are only reported) | |

**Engineering targets** (stricter than the grade warning): mean gap ≤ 3 % on ≥ 20 held-out instances with repeated seeds, 100 % independently feasible results, and an investigation of every run above 7 %. Gaps are measured to **published best-known solutions (BKS)**, which are not proven optima.

## 2. Repository layout

| Path | Contents |
| --- | --- |
| [`main.ipynb`](main.ipynb) | The deliverable: model, proof, validation, **the solver source code**, live demo and results |
| [`scripts/cvrptw_model.py`](scripts/cvrptw_model.py) | `CVRPTWInstance`, `load_cvrptw`, DIMACS distances, independent validator `check_cvrptw`, MILP residual checks, collection audit |
| [`scripts/notebook_solver.py`](scripts/notebook_solver.py) | Builds the solver cells of `main.ipynb` into an importable package |
| [`scripts/benchmark.py`](scripts/benchmark.py) | Solver protocol, isolated time-limited workers, independent scoring, campaign storage and statistics |
| [`scripts/run_alns.py`](scripts/run_alns.py) | ALNS experiments: split, parallel campaigns, reports |
| [`scripts/run_modeling.py`](scripts/run_modeling.py) | Executes the whole notebook in a fresh kernel |
| [`scripts/verify_dataset.py`](scripts/verify_dataset.py) | Audits all 356 instance/reference pairs |
| [`scripts/run_benchmarks.py`](scripts/run_benchmarks.py) | Reference-replay fixture and scoring of externally supplied solutions |
| [`scripts/watch_benchmarks.py`](scripts/watch_benchmarks.py) | Read-only live viewer of a running campaign |
| [`scripts/download_vrptw_benchmarks.py`](scripts/download_vrptw_benchmarks.py) | (Re)downloads the dataset with provenance |
| [`data/benchmarks/vrptw/`](data/benchmarks/vrptw/) | 356 `.vrp` instances + 356 paired `.sol` BKS, source manifest, licence |
| [`results/`](results/) | Committed campaigns: `alns-vnd/` (split, tuning, held-out test) and reference fixtures |
| [`reports/verification/`](reports/verification/) | Dataset and infrastructure verification evidence |
| [`tests/`](tests/) | 52 automated tests |
| [`algorithms/alns_vnd/`](algorithms/alns_vnd/) | Frozen snapshot of the solver version evaluated in `test-001` (not maintained) |
| [`docs/alns_vnd.md`](docs/alns_vnd.md) | Algorithm design notes and references |
| `outputs/` | Git-ignored scratch: executed notebooks and the generated solver build |

## 3. Setup and quick start

Python 3.9–3.12 (tested with 3.9.6). From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: py -m venv .venv ; .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

[`requirements.txt`](requirements.txt) pins numpy 2.0.2, pandas 2.3.3, matplotlib 3.9.4, vrplib 1.5.1, the notebook runner (nbformat, nbclient, ipykernel, jupyter_client), and the solver's **numba 0.60.0** (with llvmlite 0.43.0) and **psutil 7.2.2**. Numba is required: without it the notebook stops at §15.1 instead of running a ~100× slower solver.

| Task | Command |
| --- | --- |
| Run the whole notebook (strict: all 356 references must validate) | `python scripts/run_modeling.py --strict` → `outputs/main.executed.ipynb` |
| Interactive use | open `main.ipynb`, kernel `.venv`, **Restart Kernel → Run All** |
| All tests | `python -m unittest discover -v` |
| Held-out benchmark (≈2.6 h with 6 workers) | see [§10](#10-benchmarks) |

`run_modeling.py` options: `--strict` (fail on any missing pair), `--data-root PATH`, `--output PATH` (never overwrites `main.ipynb`). Without `--strict`, collection checks that cannot run are reported as **NOT RUN** (never PASS) while synthetic examples still execute; malformed data always fails. A full strict run takes ≈35 s (≈50 s the first time, when the solver compiles). The data are already in the repository; no download happens during Run All.

**Environment variables:** `ECOROUTE_PROJECT_ROOT`, `ECOROUTE_DATA_ROOT` (paths), `ECOROUTE_STRICT_DATA=1` (strict mode), `ECOROUTE_DEMO_ITERATIONS` (demo budget, default 12,000), `ECOROUTE_DISABLE_JIT=1` (run kernels as plain Python), `ECOROUTE_ALLOW_PURE_PYTHON=1` (let the demo run without Numba).

## 4. The notebook, section by section

| § | Content |
| --- | --- |
| 0 | Execution settings, roots, package versions |
| 1 | Graph and data; seeded synthetic generator (uniform or clustered); capacity-only teaching container `CVRPInstance`; necessary feasibility conditions ($\max q_i\le Q$, $\sum q_i\le KQ$, at least $\lceil \sum q_i/Q\rceil$ trucks) and why they are not sufficient |
| 2–3 | Decision variables and the distance objective |
| 4 | Routing constraints M0–M10, MTZ subtour elimination, traceability table, necessity/sufficiency proof, **temporal extension TW1–TW6** |
| 5 | NP-hardness (reduction from TSP) |
| 6 | Teaching validator, hand-written routes, invalid-route tests, explicit $x,y,z,u$ arrays checking every equation, zero-demand case |
| 8 | Sensitivity of the necessary conditions; model size ($O(Kn^2)$) |
| 9 | Edge cases |
| 10–10A | Loading the real instances; audit of all 356 references; C101 schedule plots; temporal test fixtures |
| 11 | Review checkpoint |
| 12 | ALNS + VND overview; solver assembly (`%%alns_source`); JIT and configuration cells |
| 13 | Search kernels: data layout, segment algebra, route maintenance, VND moves, VND, repair, destroy, ALNS iteration |
| 14 | Driver `solve()`: provenance, preprocessing, time-managed search, warm-up |
| 15 | Build and load; independent evaluation helpers; **reproducible live demo**; frozen experiment results; interpretation |
| 16 | References |

## 5. Mathematical model

**Data.** Depot 0, customers $C=\{1..n\}$, $V=\{0\}\cup C$, trucks $F=\{1..K\}$, arcs $A=\{(i,j): i\ne j\}$; distance $d_{ij}$ and travel time $t_{ij}$ (separate matrices, equal in the benchmarks; neither symmetry nor the triangle inequality is assumed); demand $q_i$, service $s_i$, window $[a_i,b_i]$, capacity $Q$, depot window $[a_0,H]$.

**Variables.** $x_{ijk}\in\{0,1\}$ arc use, $y_{ik}\in\{0,1\}$ assignment, $z_k\in\{0,1\}$ truck used, $u_{ik}\ge0$ visit order; times $A_{ik},S_{ik},D_{ik}$ (arrival, service start, departure) and depot $T_k$ (departure), $R_k$ (return). Waiting $W=S-A$ is derived.

**Objective (M0).** $\min \sum_k\sum_{(i,j)} d_{ij}x_{ijk}$.

| Rule | Constraint |
| --- | --- |
| M1 each customer once | $\sum_k y_{ik}=1$ |
| M2–M3 flow | $\sum_j x_{ijk}=\sum_j x_{jik}=y_{ik}$ |
| M4–M5 depot | $\sum_{j\in C}x_{0jk}=\sum_{i\in C}x_{i0k}=z_k$; also $y_{ik}\le z_k$ |
| M6 capacity | $\sum_i q_i y_{ik}\le Q z_k$ |
| M7–M9 MTZ | $y_{ik}\le u_{ik}\le n\,y_{ik}$, $u_{jk}\ge u_{ik}+1-(n+1)(1-x_{ijk})$ (valid even with zero demands) |
| M10 domains | binaries, no self-loops; optional symmetry breaking $z_k\ge z_{k+1}$ |
| TW1 | $0\le A_{ik},S_{ik},D_{ik}\le H y_{ik}$ |
| TW2 | $a_i y_{ik}\le S_{ik}\le b_i y_{ik}$, $S_{ik}\ge A_{ik}$, $D_{ik}=S_{ik}+s_i y_{ik}$ |
| TW3 | $a_0 z_k\le T_k\le R_k\le H z_k$ |
| TW4–TW6 | $\lvert A_{jk}-D_{ik}-t_{ij}\rvert\le M_{ij}(1-x_{ijk})$ for customer arcs, depot departures ($T_k$) and returns ($R_k$), with $M_{ij}=H+t_{ij}$ |

The earliest schedule (leave at $a_0$, start at $\max(A,a_i)$) decides whether a route order is feasible. **Size:** $K(n+1)^2$ binaries and $4Kn+2K$ continuous variables, so the MILP defines the problem but is not used to solve 1,000-customer instances. **Complexity:** TSP reduces to CVRPTW (one truck, unit demands, $Q=n$, zero service, wide windows), so optimisation is NP-hard and the distance-budget decision version is NP-complete.

## 6. Data and scoring

[PyVRP/Instances VRPTW](https://github.com/PyVRP/Instances/tree/main/VRPTW): Solomon (56 instances × 100 customers) and Gehring–Homberger GH200, GH400, GH600, GH800, GH1000 (60 each), each with a published BKS. Classes: **C** clustered, **R** random, **RC** mixed customer locations; type **1** has a short scheduling horizon (many short routes), type **2** a long one (few long routes). The file's `VEHICLES` (K) always exceeds the BKS route count, so in practice the fleet limit does not bind.

* Parsed with `vrplib.read_instance(path, compute_edge_weights=False)`. Disk IDs 1..N become internal 0..n (depot 0); `.sol` customer labels are already 1..n. A scalar service time applies to customers only.
* **DIMACS scoring:** each arc is $\lfloor 10\cdot\text{Euclidean}\rfloor/10$ (integer tenths, exact integer square-root boundary correction); distance = travel time; route costs are summed in integer tenths. This reproduces C101 = 827.3, C1_2_1 = 2698.6 and all 356 BKS.
* `check_cvrptw` independently checks IDs, coverage, duplicates, fleet size, load, earliest (or supplied) schedules, windows, depot return and distance (tolerance 1e-7), and gives **no score** to an infeasible solution. Dataset digest: `73cc1077…0549`.

## 7. Algorithm 1 — ALNS + VND

Adaptive Large Neighbourhood Search (Ropke & Pisinger 2006) repeatedly destroys and repairs part of the solution; every candidate is then polished by a Variable Neighbourhood Descent (Hansen & Mladenović 2001).

### 7.1 Where the code lives

The solver is written **only** in `main.ipynb` (§12–14): every cell headed `%%alns_source <module> <part>` is solver code (modules `_jit`, `config`, `kernels`, `solver`). Running these cells records them; `load_alns()` (§15.1) passes them to `scripts/notebook_solver.py`, which writes the package `outputs/alns_build/alns_notebook/` (generated and git-ignored; a file is rewritten only if its cell changed) and imports it. Numba caches compiled code next to those files, so the first run after an edit compiles once (≈15–60 s) and later runs are ready in ~0.1 s. The tests and `run_alns.py` build and run the same notebook code.

### 7.2 Search state and feasibility

* **Routes** are doubly linked lists of customers (depot = sentinel 0) in at most $R=\min(K,n)$ route slots, so the fleet limit can never be exceeded.
* **States are always feasible** (capacity and windows). A customer that cannot be inserted anywhere stays *unassigned* with a large penalty; such a state is never returned.
* **O(1) time-window checks** (Vidal et al. 2013): a visit sequence is summarised by (minimum duration $D$, time warp $TW$, earliest start $E$, latest start $L$). Two sequences joined by travel $t$ combine in constant time with $\Delta=D_1-TW_1+t$, $TW=TW_1+TW_2+\max(E_1+\Delta-L_2,0)$, $D=D_1+D_2+t+\max(E_2-\Delta-L_1,0)$; a route is feasible iff $TW=0$. Every customer stores its prefix (depot→u) and suffix (u→depot) segment, so inserting a customer or exchanging route pieces is checked without walking the route; intra-route moves are re-verified exactly. Time warp must be ≤ 1e-9 and improvements must exceed 1e-7.
* **Granular neighbours:** for each customer, the 40 closest customers by $d_{ij}$ + 0.2·forced waiting + 1.0·lateness (symmetrised); the VND uses the first 20.

### 7.3 One run of `solve(instance, config, seed, time_limit)`, step by step

1. **Budget.** Deadline = start + `time_fraction`·limit − `time_reserve` (0.97 and 0.75 s). The start is the `solve()` call (`clock="call"`) or the process start (`clock="process"`, used by benchmark workers so that start-up counts).
2. **Preprocessing.** Arrays of distances, travel times, windows, service and demand; the granular neighbour lists; the 100 nearest neighbours (string removal); the 100 most related customers (Shaw relatedness = 9·distance + 3·window difference + 2·demand difference, each normalised); the cost of serving each customer alone. The random generator is seeded with `seed`.
3. **Construction.** Parallel cheapest insertion of all customers (regret-1; candidate routes = routes of the customer's neighbours plus one empty route, all routes if none fits), then VND. This becomes the *current* and *best* solution.
4. **Temperature.** $T_{start}=1.5\,\bar d$ and $T_{end}=0.02\,\bar d$, where $\bar d$ = initial cost / (n + routes) is the mean arc length; $T$ decays exponentially with the elapsed fraction of the budget (of the iterations in deterministic mode).
5. **ALNS iterations**, run in Numba in chunks of about 50 ms between clock checks:
   1. copy the current solution;
   2. pick a **destroy** and a **repair** operator by roulette on their adaptive weights;
   3. remove $q\in[5,\min(40,0.2n)]$ customers (string removal sizes itself), keeping any still-unassigned customers in the pool;
   4. reinsert them with the repair operator;
   5. if every customer was placed, run the **VND** to a local optimum;
   6. **accept**: a new best always (score 33), a better solution (score 9), an equal one (no score), a worse one with probability $e^{-\Delta/T}$ (score 13);
   7. every 100 iterations, update each weight $w\leftarrow\max(10^{-3},\,0.9\,w+0.1\cdot\text{score}/\text{uses})$.
6. **Stop** at the deadline or after `max_iterations`.
7. **Result.** Best routes (customer IDs 1..n); cost recomputed in DIMACS integer tenths; status `completed` (or `no_solution` if a customer stayed unassigned); a trace of the best cost over time and iterations; metadata with the full configuration, iterations, stop reason, construction time, time to best, final operator weights, statistics, source hashes and whether the run is reproducible.

| Destroy | Removes |
| --- | --- |
| random | q random customers |
| worst | customers with the largest distance saving (rank $y^3$); **disabled** in the frozen configuration |
| Shaw | customers related to a random seed customer (rank $y^6$ in its relatedness list) |
| string (SISR) | short strings (≤ 10 customers, ~10 removed on average, optionally split around kept customers) from routes near a seed customer (Christiaens & Vanden Berghe 2020) |
| route | one whole random route (lets the fleet shrink) |

| Repair | Inserts |
| --- | --- |
| greedy | cheapest insertion first |
| regret-2 / regret-3 | the customer with the largest $\sum_{h=2}^{k}(c_h-c_1)$ first, so hard-to-place customers go early |
| blink | SISR greedy insertion in a random order rule (random, demand, far, close, window width), skipping each position with probability 1 % |

Insertion costs are cached per (customer, route) and only the changed route is recomputed; within a route the scan stops once the customer can no longer be reached in time.

**VND** (first improvement, 20 granular neighbours, in this order): **relocate** (a customer after/before a neighbour, or alone into an empty route) → **swap** → **2-opt\*** (tail exchange between two routes, both orientations) → **or-opt** (strings of 2–3, forward or reversed) → **2-opt** (intra-route reversal). After a pass that improves, the descent restarts at relocate; it ends at a local optimum of all five. Per-route modification stamps skip customer pairs whose routes have not changed, so re-optimising after an ALNS move only touches the affected region.

### 7.4 Configuration (defaults = frozen benchmark configuration)

All parameters are fields of `ALNSConfig` (§12.2); unknown keys are rejected.

| Group | Parameters (default) |
| --- | --- |
| Stopping | `clock` ("call"), `time_fraction` (0.97), `time_reserve` (0.75 s), `max_iterations` (0 = time only), `deterministic` (False), `chunk_seconds` (0.05) |
| Neighbourhoods | `n_neighbours` (40), `vnd_neighbours` (20), `near_list` (100), `shaw_list` (100), `tw_wait_weight` (0.2), `tw_warp_weight` (1.0), `insert_all_routes` (False) |
| Destroy | `destroy_min` (5), `destroy_max` (40), `destroy_max_fraction` (0.2), `worst_randomness` (3), `shaw_randomness` (6), `shaw_weights` (9, 3, 2), `sisr_avg_removed` (10), `sisr_max_string` (10), `sisr_split_rate` (0.5), `sisr_split_depth` (0.01), `blink_rate` (0.01) |
| Adaptive weights | `destroy_weights` random/worst/Shaw/string/route (1, 0, 1, 1, 0.5), `repair_weights` greedy/regret-2/regret-3/blink (1, 1, 1, 1), scores `score_new_best`/`score_better`/`score_accepted` (33, 9, 13), `reaction` (0.1), `segment` (100) |
| Acceptance | `temp_start` (1.5), `temp_end` (0.02), `restart_after` (0 = off) |
| VND | `neighbourhoods` (relocate, swap, two_opt_star, or_opt, two_opt) |

**Deterministic mode** (`deterministic=True` with `max_iterations`): the temperature follows the iteration count and chunks are fixed at 100 iterations, so a seed gives exactly the same solution on any machine; the time limit is only a safety cap.

## 8. Live demonstration (notebook §15)

§15.1 builds and loads the solver, refuses to continue without Numba, and warms it up on a 5-customer instance. §15.3 solves four **development** instances (Solomon/R102, Solomon/RC107, GH200/RC2_2_8, GH400/R1_4_10) with seed 0 and 12,000 iterations in deterministic mode (≈25 s in total). It validates every result with `check_cvrptw` (an infeasible result stops the notebook), re-runs the first instance to show identical routes, and plots the routes and gap-versus-iteration curves. Current output: R102 1466.6 (0.000 %), RC107 1207.8 (0.000 %), RC2_2_8 2172.2 (0.976 %), R1_4_10 8294.0 (2.676 %). These short runs are not the benchmark (which gave 30–300 s per instance), so their gaps are higher. §15.4 loads the committed campaigns and §15.5 interprets them.

## 9. Parameter tuning

<!-- To be written. -->

## 10. Benchmarks

### 10.1 Protocol

* **Split** ([`results/alns-vnd/split.json`](results/alns-vnd/split.json), seed 20261110, frozen before any tuning): within each of the 36 groups (6 sizes × 6 classes), one instance is drawn for **test** and one for **development**; the other 284 form an untouched **reserve** (a fresh test set if the algorithm ever has to change after testing). Tuning used development instances only, and the configuration was committed before the test ran.
* **Budget:** `time_limit = max(10, 0.3 × customers)` s — 30, 60, 120, 180, 240, 300 s for 100–1,000 customers; 10 seeds (0–9) per instance.
* **Execution:** `scripts/run_alns.py run` builds the notebook solver into `<campaign>/solver/` (the code is frozen and archived with the results), warms the Numba cache, writes the manifest (code commit, source and dataset hashes, environment) and launches one shard per (instance, seed) on parallel workers. Each shard calls `scripts.benchmark.run_campaign`, which runs the solver in a **freshly spawned process with a hard wall-clock kill** (start-up included, `clock="process"`). The solver only receives the instance, configuration, seed and limit — never reference routes or costs.
* **Evaluation:** `evaluate_solution` re-validates every returned route with `check_cvrptw`, recomputes the DIMACS cost, compares it with the solver's claim, re-validates the BKS and computes `gap = 100 · (cost − BKS) / BKS`. Infeasible, missing, crashed or late attempts stay in every denominator.
* **Storage:** per attempt `config.json`, `result.json`, `routes.json`, `schedule.json`, `trace.json`, `log.json` with checksums; per campaign `manifest.json`, `split.json`, `runs.jsonl/csv`, `summary.csv`, `comparison.*`, `family_summary.csv`, `paired_comparisons.json`, plus the ALNS report `alns_report.md`, `alns_instances.csv`, `alns_families.csv`, `alns_classes.csv`, `alns_overview.json`, `alns_gaps.png`, `alns_convergence.png`. Raw per-attempt folders (`shards/`) are git-ignored and archived locally as `results/alns-vnd/archives/*.tar.gz` (SHA-256 stored next to each campaign; no off-device copy yet).
* **Verdict:** PASS requires ≥ 20 held-out instances, all planned attempts feasible and within budget, verified references, an equal-weight mean gap ≤ 3 % and a documented investigation of any run above 7 %.

```bash
python scripts/run_alns.py split --output results/alns-vnd/split.json        # already done (seed 20261110)
python scripts/run_alns.py run --split-file results/alns-vnd/split.json --split test \
    --seeds 0 1 2 3 4 5 6 7 8 9 --time-per-customer 0.3 --min-time 10 --workers 6 \
    --output results/alns-vnd/<new-id>
python scripts/run_alns.py report results/alns-vnd/<new-id>                   # rebuild the ALNS report
python scripts/watch_benchmarks.py --campaign results/alns-vnd/<new-id>       # optional live viewer
```

`run` options: `--split development|test|reserve`; filters `--instances`, `--families`, `--classes`; `--seeds`; `--time-per-customer`; `--min-time`; `--config '{json}'` or `--config-file` (override `ALNSConfig`); `--variant`; `--workers` (default: half the CPUs); `--data-root`. A campaign directory must be new; nothing is overwritten.

### 10.2 Results — held-out campaign `test-001`

36 test instances × 10 seeds; Apple M2 Max (8P + 4E cores, 64 GB), 6 concurrent single-threaded workers, Python 3.9.6, Numba 0.60.0; solver code at commit `95fbd3d`.

| Metric | Value |
| --- | ---: |
| Attempts / independently feasible / within hard limit | 360 / **360** / 360 (minimum slack 1.6 s) |
| **Mean gap (equal weight per instance)** | **0.654 %** |
| Median instance gap / P90 run gap / worst run | 0.496 % / 1.448 % / 2.364 % (GH600/R2_6_3) |
| Mean best-of-10 gap / mean seed-to-seed SD | 0.389 % / 0.200 pp |
| Runs above 7 % / negative gaps | none / none |
| Shared evaluator assessment | **PASS** (quality; no runtime target agreed) |

| Customers | Limit | Mean gap | Worst run | | Class | Mean gap | Worst run |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: |
| 100 | 30 s | 0.262 % | 0.998 % | | C1 | 0.413 % | 1.679 % |
| 200 | 60 s | 0.293 % | 1.014 % | | C2 | 0.216 % | 0.861 % |
| 400 | 120 s | 0.446 % | 1.567 % | | R1 | 0.845 % | 1.731 % |
| 600 | 180 s | 0.844 % | 2.364 % | | R2 | 0.928 % | 2.364 % |
| 800 | 240 s | 0.881 % | 1.793 % | | RC1 | 0.902 % | 2.026 % |
| 1000 | 300 s | 1.198 % | 2.079 % | | RC2 | 0.619 % | 1.737 % |

Per-instance tables and plots: [`results/alns-vnd/test-001/alns_report.md`](results/alns-vnd/test-001/alns_report.md).

**Interpretation.** Every run is feasible and seeds differ by only ~0.2 pp. The BKS is matched on several clustered instances. The gap grows with size while iterations per second fall roughly in proportion to it, and the convergence curves are still descending at the deadline for 600–1,000 customers, so those sizes are limited by time rather than stuck. The weakest cases are random and mixed geography (R1, R2, RC1) at 600–1,000 customers.

**Limitations.** BKS are not proven optima and no lower bound is computed; the 0.3 s/customer budget is our own choice; there are 6 instances per size and per class; timings were measured with 6 workers sharing one machine; no PyVRP baseline yet; nothing above 1,000 customers.

### 10.3 Other evaluation tools

```bash
python scripts/verify_dataset.py --output reports/verification/<new-id>            # audit all 356 pairs
python scripts/run_benchmarks.py --reference-fixture --output results/<new-id>      # replay published routes
python scripts/run_benchmarks.py --manifest campaign.json --output results/<new-id> # score external solutions
python scripts/download_vrptw_benchmarks.py --destination data/benchmarks/vrptw     # only to (re)download data
```

* `verify_dataset.py` writes per-instance CSV/JSON, hashes, environment and evaluator sources, and exits non-zero on any failure.
* The **reference fixture** replays the published routes of 20 test + 1 development instance × 2 seeds through the same pipeline: it tests scoring and storage (zero gap expected) and can never earn a solver-quality PASS.
* The **manifest** mode scores saved `.sol`/JSON solutions from an external solver; its JSON format is in [AGENTS.md §9](AGENTS.md).
* `watch_benchmarks.py` (`--campaign`, `--interval`, `--save`) shows progress, ETA and running gaps of a campaign (by default the newest one across worktrees) without modifying it.

## 11. Tests

`python -m unittest discover -v` runs 52 tests:

* `test_model.py` — instance validation, DIMACS boundaries, schedules, windows, depot, fleet, capacity, MTZ subtours, temporal residuals;
* `test_benchmark.py`, `test_integration.py`, `test_alns_reporting.py` — scoring, isolated workers (errors, crashes, timeouts), campaign storage, command-line tools, report metrics;
* `test_alns_vnd.py` — the notebook solver: every VND move compared with a brute-force reference judged by `check_cvrptw` on symmetric, tight-window and asymmetric instances; prefix/suffix feasibility versus simulation; destroy/repair/VND consistency; local optimality; fleet-limit, single-customer, asymmetric and time-limit cases; C101 quality; configuration validation;
* `test_notebook_solver.py` — solver cells well formed; the build rewrites only changed files and re-imports them; deterministic mode is reproducible.

## 12. Status and open items

Done: model and proof (tutor sign-off pending), dataset audit, shared evaluator, ALNS + VND with a held-out PASS. Open: tutor acknowledgement of the selected scope, the parameter-tuning write-up (§9), a pinned PyVRP baseline at equal budgets, an agreed runtime budget, an off-device archive for raw results, Algorithms 2–3 (ILS and HGS, awaiting approval), and optional stress tests above 1,000 customers.
