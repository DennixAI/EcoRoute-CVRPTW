# EcoRoute — Dataset and Benchmark Contract

> **Status:** project dataset specification and agent decision guide, 2026-11-07.  
> **Target problem:** time-dependent capacitated vehicle routing with time windows (**TD-CVRPTW**).  
> **Selected static benchmark families:** **Solomon** and **Gehring–Homberger** VRPTW.  
> **Implementation status:** documentation/selection, **not** a claim that the full dataset collection has been downloaded or that an advanced solver has been implemented.  
> **Read with:** [`sources.md`](sources.md), [`context.md`](context.md), and [`README.md`](README.md). Those older documents may still reflect the previous Level B CVRP-only scope; the latest user-selected goal is the advanced capacity + time windows + time-dependent traffic model. Do not treat the older scope language as a ban on the new objective.

## 1. Executive decisions for all coding agents

1. **Develop against Solomon VRPTW; scale on Gehring–Homberger VRPTW.** These are the primary datasets because **both already include vehicle capacity, customer demand, delivery windows, service durations, a depot, and coordinates**. Do not use classical CVRP-only datasets as a substitute for time-window evaluation.
2. Keep **one configurable shared vehicle capacity `Q` per instance**, with **at most `K` available trucks** in the benchmark conventions; the solver chooses how many to activate. `K`, `Q`, customer count, demands, and scheduling data are *data*, not hard-coded constants. Tutor confirmation of fleet semantics for any nonbenchmark use remains appropriate.
3. Each nondepot customer must be **served exactly once**; no split deliveries. All used vehicles start at depot `0`, return to depot `0`, satisfy capacity and all temporal constraints, and never serve outside a hard time window.
4. **The published Solomon/Homberger travel times are static**: travel time equals Euclidean distance under each reference evaluator's precision convention. **No hourly congestion, road segments, true geographic coordinates, live speeds, or actual traffic forecasts** are supplied by these files.
5. Maintain **three separate experiment tracks**: **(A)** native static VRPTW, **(B)** the same base data augmented with a declared time-dependent traffic model, and **(C)** optional purpose-built TD-VRPTW benchmark families if independently validated. Never use static published optimum/BKS as the optimum of a modified traffic instance.
6. **Benchmark convention is part of the dataset identity.** CVRPLIB's VRPTW catalog and SINTEF's historical benchmark tables use **different objective/rounding conventions**. Pin the source and evaluator before computing gaps; see §7.
7. Separate **development/tuning** from **held-out final evaluation**. The CESI brief requires **at least 20 distinct evaluated instances**; multiple random seeds on one instance are not distinct instances.
8. Treat every resulting dataset, schedule, benchmark score, and feasibility check as **versioned and reproducible**. No fabricated optimal values, source labels, or experimental achievements.

## 2. Why these datasets, and which are in scope

CESI's assignment specifies identical-capacity trucks for the basic version, adds delivery time windows and waiting for the advanced CVRPTW level, describes predicted traffic across road segments/time slots in the project context, and requires reference-instance validation with `vrplib`, comparisons to reference solutions, and at least 20 distinct instances. The original French assignment is preserved in [`sources.md`](sources.md). It also states that instances are supplied for both variants, but **their separate CESI distribution location has not been established** from the assignment text. The public benchmarks below are independently usable.

| Role | Dataset | Required fields | Status / use |
| --- | --- | --- | --- |
| **Primary development** | Solomon, canonical 100-customer VRPTW set | Depot, XY, demand, `K`, `Q`, open/close, service time | **Selected**; parser, validator, first routing algorithm, regression tests |
| **Primary scalability benchmark** | Gehring–Homberger VRPTW | Same field types, larger `n` | **Selected**; held-out quality/runtime experiments at `n = 200, 400, 600, 800, 1000` |
| **Optional smaller sanity tests** | Solomon 25/50-customer variants | Same format or subsets depending on the published package | Optional smoke tests; **not** additional members of the canonical 56-instance 100-customer set |
| **Traffic-aware research extension** | MAMUT-routing TDVRPTW families (e.g., Dabia2013, Lera2026, Poryos2026) | Time-dependent travel model plus routing constraints; family-specific formats | **Candidate, not yet adopted**; investigate format, reference checker, licensing, objective and computational cost before integration |
| **Not the primary advanced testbed** | Classical CVRP families (A/B/X/XL) | Capacity and demand, generally no time windows | May support a **separate basic-CVRP regression track**, not evidence of VRPTW/TD-VRPTW correctness |

**Important:** An instance file is both **input data on which to run our algorithm** and, when paired with a comparable published reference solution, **a benchmarking case**. The difference is whether it belongs to the tuning partition or the held-out evaluation partition—not whether it is a special “benchmark-only” file.

## 3. Solomon and Homberger: family inventory

| Property | Solomon (1987) | Gehring–Homberger (1999/2005 collections) |
| --- | --- | --- |
| Canonical instances | **56** | **300** |
| Customers per instance | **100** | **200, 400, 600, 800, 1000** |
| Instances at each size | 56 at 100 | **60 per size** = 6 subclasses × 10 instances |
| Total locations, including depot | **101** | **201, 401, 601, 801, 1001** |
| Depots | **1**, node `0` | **1**, node `0` |
| Maximum available vehicles (`K`, as specified in the files) | **25** | Usually **50, 100, 150, 200, 250** for the five sizes respectively; **read the file** |
| Truck capacity (`Q`) | Same for all vehicles **within an instance**; varies by category | Same within an instance; varies by category |
| Customer data | Coordinates, nonnegative delivery demand, earliest/latest service start, service duration | Same data schema |
| Geography | Artificial Cartesian 2D test area, class-dependent clustering | Artificial Cartesian 2D geography, class-dependent clustering; larger constructions |
| Native interstop travel | Static Euclidean, travel time = distance | Static Euclidean, travel time = distance |
| Real road network / hourly traffic | **Absent** | **Absent** |
| Common file layout | Solomon-format plaintext, often `.txt` | Solomon-compatible plaintext, often `.txt` |
| Reference results | Published benchmark tables and some route listings; source-dependent conventions | Published benchmark tables and some route listings; source-dependent conventions |

A `100`-customer Solomon instance means **100 mandatory customers plus one depot**, not 100 locations in total. Likewise a Homberger 1000-customer instance has **1001 locations**. The six categories in **both** families are:

| Class | Customer placement | Temporal / loading pattern | Typical `Q` |
| --- | --- | --- | ---: |
| **C1** | Clustered (`C`) | Shorter planning horizon / tighter windows; fewer visits per route | 200 |
| **C2** | Clustered (`C`) | Longer horizon / wider windows; more visits per route | 700 |
| **R1** | Random/uniformly dispersed (`R`) | Shorter horizon / tighter windows | 200 |
| **R2** | Random/uniformly dispersed (`R`) | Longer horizon / wider windows | 1000 |
| **RC1** | Mixed clustered + dispersed (`RC`) | Shorter horizon / tighter windows | 200 |
| **RC2** | Mixed clustered + dispersed (`RC`) | Longer horizon / wider windows | 1000 |

These capacities are **family-specific reference values**, **not** required global defaults. Always trust the parsed file over this descriptive table. Not every customer necessarily has a narrow window: inspect each actual `READY TIME`/`DUE DATE`. Types `1` and `2` differ in more than one factor (capacity, horizon, window structure); **do not claim that a performance difference is caused by window width alone** without controlling for other changes.

### Instance naming patterns

- **Solomon:** `C101`, `C102`, `C201`, `R101`, `R201`, `RC101`, `RC201`, etc. `C/R/RC` indicates geography; the next digit `1/2` is the subclass; final digits identify the instance. Case and extensions may vary by source.
- **Homberger:** `C1_2_1`, `R2_4_3`, `RC1_10_10`, etc. The middle number is a *size code*: `2=200`, `4=400`, `6=600`, `8=800`, `10=1000`; the last number identifies one of ten cases in that class/size group. SINTEF displays some names in lowercase.
- **Solomon canonical class counts:** C1=9, C2=8, R1=12, R2=11, RC1=8, RC2=8 (**56** total).
- **Homberger:** 10 instances for each of 6 classes at each of 5 sizes (**300** total).

**Geographic caution:** Neither family's XY coordinates are latitude/longitude or an OpenStreetMap road network. No guarantee of a universal kilometer/meter scale or a direct real-city map. Compute and report actual bounding boxes, nearest-neighbor distances, clustering statistics, and scatterplots **from each file** rather than assigning a physical area or customer density without data.

## 4. Raw file structure and required interpretation

Both families use the **Solomon text format**. The following is a **made-up structural illustration, not a real benchmark instance**:

```text
DEMO_ONLY

VEHICLE
NUMBER     CAPACITY
  2          40

CUSTOMER
CUST NO.  XCOORD.  YCOORD.  DEMAND  READY TIME  DUE DATE  SERVICE TIME
  0           50       50        0        0         300          0
  1           55       52       10       20          70         10
  2           62       48       20       45         115          5
```

| Raw field | Canonical meaning | Notes for implementation |
| --- | --- | --- |
| First text line | Instance identifier | Preserve original identifier and source filename |
| `VEHICLE` → `NUMBER` | `K`: **maximum available vehicles** | Use up to `K`; inactive trucks need not be dispatched |
| `VEHICLE` → `CAPACITY` | `Q`: capacity shared by the fleet | Configurable **per instance**; no default fleet heterogeneity |
| `CUST NO.` | Node ID | Standard files use `0` for depot and `1..n` for customers |
| `XCOORD.`, `YCOORD.` | 2D synthetic coordinates | Use for Euclidean distance and plotting, not GPS |
| `DEMAND` | Nonnegative load delivered to a customer | Depot demand normally `0`; unsplittable demands |
| `READY TIME` | Earliest permitted **service start** `a_i` | Vehicle arriving early may wait |
| `DUE DATE` | Latest permitted **service start** `b_i` | **Not necessarily** latest completion; follow benchmark's precise definition |
| `SERVICE TIME` | Service duration `s_i` | Added to service-start time before onward travel |
| Depot row `0` | Depot coordinates, window, demand, service | Trucks depart from and return to depot; respect depot close/return deadline |

All raw numeric constants are described as integer-valued by SINTEF; **derived Euclidean distances/times are fractional**. Interpret the synthetic temporal values as **elapsed benchmark time units**, not wall-clock timestamps or European time zones. Native tests use the benchmark convention **one distance unit of travel corresponds to one travel-time unit**. Do **not** label them minutes/kilometers without an explicit conversion assumption.

### Canonical model data contract for the solver

Normalize the parser output to a single internal instance schema, regardless of family or source. A suggested contract (design, **not yet implemented**) is:

```python
VRPTWInstance(
    name: str,
    family: str,                 # solomon | homberger
    source: str,                 # archive URL + archive/member path
    n_customers: int,
    depot_index: int,            # 0 for standard Solomon-format instances
    coordinates: array[N, 2],   # N = n_customers + 1
    demands: array[N],          # demands[0] == 0
    time_windows: array[N, 2],  # [earliest_service_start, latest_service_start]
    service_durations: array[N],
    vehicle_count: int,         # maximum available, K
    vehicle_capacity: float,    # one shared Q
    distance_policy: str,       # e.g. 'sintef_full_precision'
    benchmark_source: str,      # CVRPLIB or SINTEF, for reference evaluation
)
```

Keep identifiers stable across parser, solver, animation, route outputs, and reference files. Make units, float tolerances, and evaluator policies explicit. **Do not** silently convert the input into a static CVRP by dropping `time_windows` or `service_durations`.

## 5. Loading the files in Python

The `vrplib` project is a **file parser and writer**, not the optimizer and not the dataset archive. It supports Solomon and Homberger formats via the same parser.

```bash
pip install vrplib numpy
```

```python
from pathlib import Path
import numpy as np
import vrplib

path = Path("data/raw/solomon/C101.txt")  # after you actually download it
instance = vrplib.read_instance(str(path), instance_format="solomon")

coords = np.asarray(instance["node_coord"], dtype=float)
demands = np.asarray(instance["demand"], dtype=float)
windows = np.asarray(instance["time_window"], dtype=float)
services = np.asarray(instance["service_time"], dtype=float)
K = int(instance["vehicles"])
Q = float(instance["capacity"])

assert coords.ndim == 2 and coords.shape[1] == 2
N = len(coords)
assert len(demands) == N and windows.shape == (N, 2)
assert len(services) == N and N > 1
assert K >= 1 and Q > 0
assert np.all(np.isfinite(coords)) and np.all(np.isfinite(windows))
assert np.all(np.isfinite(demands)) and np.all(np.isfinite(services))
assert np.all(demands >= 0) and np.all(services >= 0)
assert np.all(windows[:, 0] <= windows[:, 1])
assert demands[0] == 0
assert np.all(demands[1:] <= Q)  # necessary for individual deliveries

# Use data, never a hard-coded 25/50/100/200/1000 in the solver.
n_customers = N - 1
print(path.name, n_customers, "customers", K, "trucks available", "Q=", Q)
```

`vrplib.read_instance` also computes `edge_weight` from Euclidean coordinates by default. **Do not assume its default edge weights match your chosen benchmark's rounding rule.** Construct or evaluate distance with the pinned convention in §7. Preserve raw input and original IDs; keep any transformed representation separate. **Do not assume** a published `.sol` is always available for every instance: reference tables and route files have different coverage.

Suggested future repository layout (not a claim that these folders already exist):

```text
project-root/
  dataset.md                     # this source-of-truth dataset contract
  data/
    raw/
      solomon/                   # original, unmodified .txt + provenance
      homberger/                 # original, unmodified .txt + provenance
    manifests/                   # source URL, SHA-256, size, split, reference policy
    derived/
      traffic/                   # reproducible, generated TD overlays
  src/                            # parser, normalizer, evaluator, solver
  tests/                          # fixture, parsing, objective and feasibility tests
  results/                        # immutable per-run results + metadata
```

Do not commit large downloaded archives or generated matrices automatically. Check source terms, size limits, and repository policy first.

## 6. Feasibility semantics that agents must implement

Let `0` be the depot, `C={1,...,n}`, `q_i` customer demand, `Q` common capacity, `[a_i,b_i]` permitted **service-start** window, and `s_i` customer service duration. For a used truck following `0 -> i1 -> ... -> ip -> 0`:

1. **Visit coverage:** every customer belongs to exactly one used truck's route (no split deliveries, no omitted or repeated visits).
2. **Capacity:** `sum(q_i for i in route) <= Q`, including zero-demand visits if any. `sum_i q_i <= K*Q` and `max_i q_i <= Q` are **necessary, not sufficient**, for feasible packing.
3. **Fleet:** number of used routes `<= K`; no empty-route penalty unless explicitly modeled.
4. **Arrival:** `arrival_i = depart_previous + travel_time(previous, i, depart_previous)`.
5. **Waiting/service:** `service_start_i = max(arrival_i, a_i)`; `service_start_i <= b_i` with a documented numerical tolerance; `depart_i = service_start_i + s_i`.
6. **Depot:** each truck's starting time respects depot opening; it must return no later than the applicable depot deadline (and satisfy any configured vehicle shift rule). Depot row is not an ordinary delivery customer.
7. **Static benchmark travel time:** `travel_time(i,j,t) = d_ij` independent of `t`; native distance is Euclidean under the selected policy.
8. **Time-dependent extension:** `travel_time(i,j,t) = tau_ij(t)` computed from a separately specified and validated congestion scenario. All downstream schedule times must be recomputed after route moves or departure-time changes.

**Example:** A truck arriving at customer `i` at 09:45 with window [10:00, 12:00] may wait and begin service at 10:00. The end of service may be later than 12:00 **if the selected benchmark uses a latest-service-start interpretation**; do not silently enforce latest-completion instead. A customer arriving after 12:00 cannot be served under hard windows. In benchmark time units, replace clock examples by numeric equivalents.

**Validator:** implement a standalone `check_solution(instance, routes, departure_times, travel_policy)` that independently recomputes coverage, per-route load, exact timeline, waiting, last permitted service starts, return times, and objective. Do not rely only on the solver's internal feasibility flags. Add malformed cases: missed deadline, depot late return, overload, duplicate/missing customer, wrong node IDs, impossible individual demand, zero-demand customer, early arrival, nonzero service duration, inactive truck, floating-point boundary, and traffic interval crossing.

## 7. Benchmark protocols: **do not mix incompatible standards**

This is the most important experimental caveat. The same named dataset can yield **different reference numbers** under different legitimate conventions.

### Protocol A — CVRPLIB VRPTW catalog (recommended for **distance-only** comparisons)

CVRPLIB currently publishes Solomon (56) and Homberger (300) under the following documented conventions:

- Objective: **minimize total traveled distance** subject to VRPTW feasibility, with **at most `K` routes**.
- Edge distance: **Euclidean distance truncated to one decimal place** (not rounded to the nearest tenth). Define `d_ij = floor(10 * hypot(x_i-x_j, y_i-y_j)) / 10` with a carefully tested floating-point policy.
- Solution cost: aggregate distance displayed/rounded to **one decimal** according to the site.
- Reference column: **`UB`** is a published upper bound/best feasible cost; **`Opt`** indicates whether optimality is proven under that catalog convention. A best-known upper bound is **not** automatically a certified optimum.
- Example: CVRPLIB's `C101` catalog value is **827.3** under its convention; this is **not** interchangeable with SINTEF's figure below.

**Agent action:** before batch benchmarking, reconstruct published costs for at least one fully listed reference route and test the exact edge-cost policy and numerical tolerance. Treat a mismatch as a blocker, not an “improved” algorithm.

### Protocol B — SINTEF / historical Solomon–Homberger leaderboard

SINTEF publishes a **different** evaluation:

- **Hierarchical (lexicographic) objective:** first minimize number of used vehicles, **then** minimize total distance among solutions with that count.
- Euclidean distances and travel times computed with **double precision**; aggregate distance **displayed to two decimals** (do not round every arc to two decimals).
- Example: SINTEF lists `C101` with **10 routes and distance 828.94**. CVRPLIB's 827.3 is **not** a contradictory record under the *same* objective—it is a **different comparison protocol**.
- SINTEF's “best known” values are not necessarily proven optima; the source warns about historical rounding mistakes, missing full route details for some entries, and data-provenance limitations.

**Agent action:** if using SINTEF, report the result as `(vehicles_used, total_full_precision_distance)` and compare lexicographically against the same source. **Do not calculate a scalar distance gap to a hierarchical reference where your solution uses a different number of vehicles**; explain the vehicle-count difference separately. Never label all SINTEF records “proven optimal.”

### Mandatory reference metadata and gap calculation

Record `dataset_family`, `instance_name`, `source_url`, `source_file_sha256`, `reference_source`, `reference_date`, `reference_objective`, `distance_rounding`, `number_of_vehicles_used`, `reference_cost`, `reference_is_proven_optimal`, `feasible`, and `units`.

For the **same** objective, fleet policy, and cost convention, a distance-only gap to a reference cost `B > 0` is:

```text
gap_to_reference_percent = 100 * (our_distance_cost - B) / B
```

If `B` is **proven optimal**, call it an *optimality gap*. Otherwise, call it a *gap to best known* (which can in principle be negative after improving the previous BKS). A gap is meaningless if comparing different rounding policies, fleet objectives, window definitions, traffic scenarios, or units. Use raw unrounded internal costs where the benchmark specifies; round for presentation **only as prescribed**.

### Protocol C — Our new traffic-aware TD-CVRPTW experiments

A traffic-augmented Solomon/Homberger instance **is a new instance** with a different travel-time function and potentially different feasibility. **Published static `UB`, `Opt`, and SINTEF route costs are not TD optima**. Report:

- Explicit primary time objective (e.g., sum of vehicle elapsed route durations, with all waiting and service effects defined), plus total distance, driving time, waiting, vehicles used, feasibility, and runtime.
- The exact traffic profile, departure policy, time horizon, seed/version, and all parameters.
- Comparisons only to feasible algorithms or baselines on the **same traffic instance**, or to a proven TD optimum if actually established.
- Traffic sensitivity and solution robustness, with honest infeasibility reporting. **Do not force a solution** when traffic makes all routes infeasible under available vehicles and deadlines.

The CESI problem statement motivates **duration with predicted traffic**, which is different from the standard VRPTW distance objective. Label results by protocol to prevent accidental cross-comparison.

## 8. Traffic-extension data: what is missing and how to supply it

The selected raw instance families lack: a real directed road graph, road-segment speed forecasts, hourly time slots, incident closures, live GPS coordinates, and a time-dependent stop-to-stop matrix. **Do not claim any of those exist in the raw `.txt` files**.

### Two supported modeling paths (decide and label explicitly)

**Path 1 — Controlled synthetic stop-to-stop time dependence (recommended for initial TD experiments):** retain Solomon/Homberger coordinates, demands, `K`, `Q`, windows, and service durations; derive directed or symmetric baseline distances; attach synthetic, **time-dependent travel-time** functions to each stop pair or a reproducible synthetic edge network. This is *not* real road-segment traffic. Ensure time units and congestion multipliers are meaningful relative to each instance's actual scheduling horizon.

**Path 2 — Explicit road-network traffic (more faithful to the assignment):** map stops to a road graph (e.g., from open map data with an explicit mapping procedure), build directed arcs, associate speed by road segment and time interval, compute time-dependent shortest paths between delivery stops, and preserve routing feasibility. Since artificial benchmark XY are not GPS, using real maps requires a documented relocation/projection or a newly generated geospatial dataset; otherwise it is invalid to pretend these coordinates are real street addresses.

For either path, the canonical extension must specify:

```text
traffic_scenario_id
base_instance_id + hash
traffic_source = synthetic | published_benchmark | real_forecast
traffic_model_name + version
random_seed (if synthetic)
time_origin and time_unit
forecast_horizon
interval_boundaries
directed_edge_or_road_segment_ids
speed_profile_or_travel_time_function
interpolation / boundary policy
missing_data_policy
FIFO_policy and validation
departure_time_policy
reference_objective + evaluator_version
```

**FIFO is important:** a later departure from the same node should not reach the same destination earlier than an earlier departure on the same FIFO road/link model. Arbitrary per-time-slot multiplication of full arc travel times can create impossible discontinuities and invalidate earliest-arrival assumptions. Implement a **time-consistent traversal model** (for example, integrate distance traveled under time-varying segment speeds across interval boundaries), test monotonic arrival functions `A_ij(t)=t+tau_ij(t)`, and document any justified non-FIFO exception. If a journey crosses multiple forecast slots, it must consume the appropriate durations in each slot or follow a clearly justified approximation.

**Time-window feasibility may change** after adding traffic. Validate and report how many derived instances remain feasible. A static reference route is not automatically feasible, much less optimal, under the altered conditions. Keep native benchmark data immutable and all traffic extensions in new files with their own names/hashes.

### Additional source worth evaluating, not yet approved as our dataset

[MAMUT-routing](https://github.com/ANR-MAMUT/MAMUT-routing) maintains **TDVRPTW** research benchmark families (including time-dependent variants related to Solomon/Homberger), a data-contract library, and independent checkers. In particular, [Lera2026](https://github.com/ANR-MAMUT/MAMUT-routing-TDVRPTW-Lera2026) is described as a 200–1000-customer time-dependent family derived from Gehring–Homberger data. It is **not** a standard Solomon `.txt` file with a new column; it uses additional time-dependent specifications and its own evaluator. Treat this as a promising separate experimental track, subject to validation of source format, provenance, licensing, feasibility repairs, objective and reference convention. Never claim to have integrated it until those checks pass.

## 9. Validation checklist for newly obtained files

On acquisition or parsing, **fail loudly** when these checks fail rather than silently repairing official benchmark data:

- [ ] Archive/source URL is documented; archive SHA-256 and individual file SHA-256 recorded.
- [ ] Instance name, family, class, claimed size, source, and file format are consistent.
- [ ] Exactly one depot at node `0`, plus `n` unique customers numbered as expected (or explicit remapping recorded).
- [ ] `N = n+1`; coordinates `(N,2)`, demands `(N,)`, time windows `(N,2)`, service times `(N,)`.
- [ ] All required values finite; `K` positive integer, `Q > 0`, no negative demands or service times, `a_i <= b_i`.
- [ ] Zero depot demand, customer loads `<= Q`; do not treat aggregate `sum(demand) <= K*Q` as sufficient for route feasibility.
- [ ] Temporal horizon/depot due date is meaningful; no time units or time zones invented.
- [ ] Parsed `K`, `Q`, nodes, sample windows and distance costs match selected source's expected instance metadata.
- [ ] Independent checker accepts at least one trusted reference route **when a matching route file exists** and its benchmark conventions match.
- [ ] All instance names have assigned immutable split (`development`, `validation`, `test`) before final tuning.
- [ ] Traffic variants have separate unique IDs, manifests, hashes, and independent reference baselines.
- [ ] No data leakage from final held-out instances into hyperparameter selection or operator ranking.

## 10. Experiment plan and agent implementation order

The following is an **intended plan**, not reported experimental progress.

| Phase | Suggested dataset slices | Required exit condition |
| --- | --- | --- |
| **1. Parser + structural exploration** | One Solomon case from each of C1/C2/R1/R2/RC1/RC2 | Parse and plot fields; validate sizes, windows, loads, depot, `K`, `Q` |
| **2. Reference validator** | Solomon C101, one dispersed, one mixed instance; trusted routes when available | Independently reproduce feasibility and source-matched objective conventions |
| **3. Basic CVRPTW algorithm** | A *declared development subset* of Solomon; more than one geographic/window class | Consistent feasible construction; local search and/or ALNS/ILS; repeated-seed tests |
| **4. Algorithm selection** | Solomon tuning/validation instances separate from final test | Compare candidate algorithms under equal budgets; choose using feasibility, quality, time |
| **5. Large static VRPTW** | Gehring–Homberger 200 → 400 → 600 → 800 → 1000 | Correctness preserved; recorded scaling, timeout and memory behavior |
| **6. Final static benchmark** | **>=20 distinct held-out instances** across all six classes and multiple sizes | Report source-matched costs, fleet counts, gaps where meaningful, timings and failed cases |
| **7. Traffic experiment** | Frozen base instances paired with multiple predeclared traffic overlays | Valid independent TD schedules; time objective, waiting, route changes, congestion sensitivity |
| **8. Optional external TD benchmark** | A validated MAMUT TDVRPTW subset | Reference objective and checker reproduced; separate results table and citations |

**Recommended holdout principle:** stratify by C/R/RC, 1/2 variants, and sizes. Reserve a final test set before tuning and keep a complete manifest. At least 20 **different instance IDs** must be included in the assessed experimental analysis. Repeated runs are additional observations of the same instance; synthetic traffic variants are explicitly distinct derived cases but should **not replace** the requirement for diversity in base instances without tutor agreement. Avoid comparing raw performance differences across sizes as though problem difficulty depends only on `n`.

### Per-run result schema

Store one machine-readable record per run containing, at minimum:

```text
instance_id, base_instance_sha256, family, size, class, split
source_url, benchmark_protocol, distance_policy, objective_definition
traffic_scenario_id_or_null, traffic_policy_version, traffic_seed_or_null
solver_name, code_commit, dependency_versions, parameter_hash, rng_seed
machine_hardware, time_budget_s, time_elapsed_s, peak_memory_mb
feasible, violated_constraints, vehicles_used, total_distance
sum_route_elapsed_time, total_driving_time, total_waiting_time
max_route_duration, total_service_time, primary_objective_value
reference_source, reference_value, reference_is_optimal, valid_gap_percent_or_null
status = success | infeasible | timeout | error
route_sequences, departure_times, service_start_times, return_times
```

Do not report zero violations without actually running the independent validator. Route animations are explanatory outputs, not feasibility certificates or empirical benchmark evidence.

## 11. Algorithm design implications of these datasets

- A **complete graph with static distances** is sufficient for *native* Solomon/Homberger CVRPTW baseline. It does not automatically represent the full traffic-aware CESI business scenario.
- The route representation must carry or recompute **per-customer schedule state**; route sequences alone are not enough for time feasibility. Waiting is **allowed**, lateness is **not**.
- Every relocate/swap/2-opt/2-opt*/insertion move potentially shifts downstream arrivals. Under time-dependent traffic, changes can also push later travel across congestion intervals. **Do not reuse static distance deltas as a substitute for schedule recomputation.**
- Use separate cost providers: `StaticDistanceProvider` and `TimeDependentTravelProvider`, with one shared route validator and an explicit primary objective per experiment.
- Validate independently on small cases; compare a simple construction baseline, a competitive local-search/metaheuristic candidate, and (when permitted) an attributed external solver **only if it supports exactly the tested constraints**.
- Large instances make full dense time-expanded costs expensive. A 1001×1001 `float64` dense matrix alone is approximately **8 MB**; 1000 such slices are roughly **8 GB**, excluding solver data, route schedules, caches, and overhead. Prefer on-demand evaluation, justified caching, candidate neighborhoods, and incremental schedule propagation.
- For the assignment's ambition of **several thousand customers**, Solomon/Homberger top out at **1000 customers**. Tests beyond that require *additional explicitly labeled* generated or other-source instances; do not claim the selected files alone prove several-thousand-customer scalability.
- Always attribute external datasets, BKS, and solver baselines. Do not report a published reference solution as a route found by our algorithm.

## 12. Verified source links and provenance

**Dataset downloads and authoritative interpretation**

1. [CVRPLIB — VRPTW dataset catalog](https://galgos.inf.puc-rio.br/cvrplib/en/vrptw/instances) — Solomon and Homberger instance names, max fleet/capacity, upper bounds, optimality flags; see [VRPTW convention description](https://galgos.inf.puc-rio.br/cvrplib/index.php/en/vrptw).
2. [SINTEF — Solomon benchmark](https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/) and [100-customer instances/download](https://www.sintef.no/projectweb/top/vrptw/100-customers/) — includes a ZIP of the original 100-customer files and independently maintained historical reference routes/results. [Solomon 100 ZIP](https://www.sintef.no/globalassets/project/top/vrptw/solomon/solomon-100.zip).
3. [SINTEF — Gehring–Homberger benchmark](https://www.sintef.no/projectweb/top/vrptw/homberger-benchmark/) — separate ZIPs and result tables for [200](https://www.sintef.no/projectweb/top/vrptw/200-customers/), [400](https://www.sintef.no/projectweb/top/vrptw/400-customers/), [600](https://www.sintef.no/projectweb/top/vrptw/600-customers/), [800](https://www.sintef.no/projectweb/top/vrptw/800-customers/), [1000](https://www.sintef.no/projectweb/top/vrptw/1000-customers/) customers. [Homberger 200 ZIP](https://www.sintef.no/globalassets/project/top/vrptw/homberger/200/homberger_200_customer_instances.zip).
4. [SINTEF — authoritative format and time-window semantics](https://www.sintef.no/projectweb/top/vrptw/documentation2/) — depot `0`, `K` maximum, shared `Q`, time-window endpoints refer to service starts.
5. [PyVRP/VRPLIB — Python loader and Solomon parser](https://github.com/PyVRP/VRPLIB) — `pip install vrplib`, `read_instance(..., instance_format="solomon")`, field mappings.
6. [DIMACS VRPTW challenge](https://dimacs.rutgers.edu/programs/implementation-challenges/vehicle-routing/implementation-challenge-vehicle-routing/vrp-with-time-windows) — corroborates 56 Solomon/300 Homberger, their customer counts, and controlled algorithm evaluation.
7. [MAMUT-routing (research datasets, optional)](https://github.com/ANR-MAMUT/MAMUT-routing) and [Lera2026 TDVRPTW family](https://github.com/ANR-MAMUT/MAMUT-routing-TDVRPTW-Lera2026) — available separately; requires different parser/evaluator and provenance review.
8. [Official CESI project assignment](https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html) and local [`sources.md`](sources.md) — assignment requirements and original text.

### Outstanding data acquisition and research tasks

- [ ] Download **unmodified** Solomon 100-customer and Homberger 200–1000-customer archives; record SHA-256 hashes, licenses/usage conditions, original filenames and acquisition date.
- [ ] Inspect a real raw file from **each** family and every selected size, confirming field types, `K`, `Q`, actual coordinate ranges and source name conventions.
- [ ] Pin **one primary static leaderboard convention** for official gap reporting (CVRPLIB **or** SINTEF); support a separate leaderboard only with a separate evaluator.
- [ ] Locate any distinct CESI-supplied instance attachments through the course resources or tutor; do not assume their absence simply because they are not in the pasted assignment text.
- [ ] Finalize realistic traffic data or a scientifically defensible, versioned synthetic profile generation method; decide whether road-level or stop-pair-level traffic is implemented.
- [ ] Validate at least one reference route and cost under the selected convention before large experiments.
- [ ] Freeze train/validation/test instance IDs, solver parameters, machine/runtime budgets, reference publication dates and provenance before final evaluation.

---

**Agent rule:** The purpose of these datasets is to drive a **correct and reproducible advanced VRP solver**, not to induce hidden assumptions from a convenient example. Keep `K`, `Q`, customer attributes, objective, traffic policy, source, and reference conventions explicit at every layer of the implementation.
