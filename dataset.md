# EcoRoute — Dataset and Benchmark Contract

> **Status:** dataset specification and agent decision guide, updated 2026-11-09.  
> **Target problem:** time-dependent capacitated vehicle routing with time windows (**TD-CVRPTW**).  
> **Selected primary data source:** [`PyVRP/Instances`](https://github.com/PyVRP/Instances), **`VRPTW/` only** — 56 Solomon + 300 Gehring–Homberger instances, with paired `.vrp` inputs and `.sol` reference solutions.  
> **Implementation status:** documentation/selection, **not** a claim that the full dataset collection has been downloaded or that an advanced solver has been implemented.  
> **Read with:** [`sources.md`](sources.md), [`context.md`](context.md), and [`README.md`](README.md). Those older documents may still reflect the previous Level B CVRP-only scope; the latest user-selected goal is the advanced capacity + time windows + time-dependent traffic model. Do not treat the older scope language as a ban on the new objective.

## 1. Executive decisions for all coding agents

1. **Use `PyVRP/Instances/VRPTW` as the primary and only required static benchmark acquisition source.** Download Solomon (56) and Gehring–Homberger (300), each with `.vrp` problem data and `.sol` reference routes. Both already encode vehicle capacity, demands, hard time windows, service duration, depot and coordinates. Do **not** download/use classical CVRP-only sets as evidence for CVRPTW performance.
2. Keep **one configurable shared vehicle capacity `Q` per instance**, with **at most `K` available trucks** in the benchmark conventions; the solver chooses how many to activate. `K`, `Q`, customer count, demands, and scheduling data are *data*, not hard-coded constants. Tutor confirmation of fleet semantics for any nonbenchmark use remains appropriate.
3. Each nondepot customer must be **served exactly once**; no split deliveries. Internally use **zero-based index `0` for the depot** and `1..n` for customers. The on-disk `.vrp` uses **one-based node IDs** (`1` for the depot, `2..N` for customers); the paired `.sol` routes list customer labels `1..n`, matching **normalized zero-based array indices**. All used vehicles return to the depot and satisfy capacity and temporal constraints.
4. **The published Solomon/Homberger travel times are static**: travel time equals Euclidean distance under each reference evaluator's precision convention. **No hourly congestion, road segments, true geographic coordinates, live speeds, or actual traffic forecasts** are supplied by these files.
5. Maintain **three separate experiment tracks**: **(A)** native static VRPTW, **(B)** the same base data augmented with a declared time-dependent traffic model, and **(C)** optional purpose-built TD-VRPTW benchmark families if independently validated. Never use static published optimum/BKS as the optimum of a modified traffic instance.
6. **Benchmark convention is part of the dataset identity.** CVRPLIB's VRPTW catalog and SINTEF's historical benchmark tables use **different objective/rounding conventions**. Pin the source and evaluator before computing gaps; see §7.
7. Separate **development/tuning** from **held-out final evaluation**. The CESI brief requires **at least 20 distinct evaluated instances**; multiple random seeds on one instance are not distinct instances.
8. Treat every resulting dataset, schedule, benchmark score, and feasibility check as **versioned and reproducible**. Run `download_vrptw_benchmarks.py` from the repository root; it saves files under `data/benchmarks/vrptw/` rather than cloning GitHub. Its manifest records the downloaded ZIP SHA-256 but **not a pinned Git commit or per-file checksums**; freeze those separately for publication. No fabricated optimal values, source labels, or experimental achievements.

## 2. Why these datasets, and which are in scope

CESI's assignment specifies identical-capacity trucks for the basic version, adds delivery time windows and waiting for the advanced CVRPTW level, describes predicted traffic across road segments/time slots in the project context, and requires reference-instance validation with `vrplib`, comparisons to reference solutions, and at least 20 distinct instances. The original French assignment is preserved in [`sources.md`](sources.md). It also states that instances are supplied for both variants, but **their separate CESI distribution location has not been established** from the assignment text. The public benchmarks below are independently usable. **The adopted files are PyVRP-converted VRPLIB `.vrp` files, not the older Solomon-format `.txt` source distributions.** Other sources remain cross-checks, not the authoritative local file layout.

| Role | Dataset | Required fields | Status / use |
| --- | --- | --- | --- |
| **Primary development** | Solomon, canonical 100-customer VRPTW set | Depot, XY, demand, `K`, `Q`, open/close, service time | **Selected**; parser, validator, first routing algorithm, regression tests |
| **Primary scalability benchmark** | Gehring–Homberger VRPTW | Same field types, larger `n` | **Selected**; held-out quality/runtime experiments at `n = 200, 400, 600, 800, 1000` |
| **Optional smaller sanity tests** | Generated or carefully documented subsets of selected `.vrp` instances | Subsets must keep valid demands, windows and fleet constraints | Optional unit fixtures, **not** part of the 356 official cases |
| **Traffic-aware research extension** | MAMUT-routing TDVRPTW families (e.g., Dabia2013, Lera2026, Poryos2026) | Time-dependent travel model plus routing constraints; family-specific formats | **Candidate, not yet adopted**; investigate format, reference checker, licensing, objective and computational cost before integration |
| **Excluded from primary downloads** | `PyVRP/Instances/CVRP` and other classical CVRP families (A/B/X/XL) | No delivery time windows | **Do not download for this selected CVRPTW dataset.** Other GitHub variants with windows (MDVRPTW, PDPTW, etc.) are distinct problems with additional constraints and also remain out of scope. |

**Important:** An instance file is both **input data on which to run our algorithm** and, when paired with a comparable published reference solution, **a benchmarking case**. The difference is whether it belongs to the tuning partition or the held-out evaluation partition—not whether it is a special “benchmark-only” file.

## 3. Selected collection: six folders, 356 instances, 712 paired files

**Primary repository:** [`https://github.com/PyVRP/Instances`](https://github.com/PyVRP/Instances); **selected subdirectory:** [`VRPTW/`](https://github.com/PyVRP/Instances/tree/main/VRPTW). Each logical instance has a `NAME.vrp` **input** and a `NAME.sol` **published reference route/cost**. The repository contains other problem families, but our downloader intentionally ignores them.

| Local directory | Upstream location | Customer count (`n`) | Nodes including depot (`N=n+1`) | `.vrp` inputs | `.sol` references | Time windows |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `Solomon/` | [`VRPTW/Solomon/`](https://github.com/PyVRP/Instances/tree/main/VRPTW/Solomon) | 100 | 101 | 56 | 56 | **Yes** |
| `GH200/` | [`VRPTW/GH200/`](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH200) | 200 | 201 | 60 | 60 | **Yes** |
| `GH400/` | [`VRPTW/GH400/`](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH400) | 400 | 401 | 60 | 60 | **Yes** |
| `GH600/` | [`VRPTW/GH600/`](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH600) | 600 | 601 | 60 | 60 | **Yes** |
| `GH800/` | [`VRPTW/GH800/`](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH800) | 800 | 801 | 60 | 60 | **Yes** |
| `GH1000/` | [`VRPTW/` root](https://github.com/PyVRP/Instances/tree/main/VRPTW) | 1000 | 1001 | 60 | 60 | **Yes** |
| **Total** | | | | **356** | **356** | **All 356** |

**Special GH1000 path rule:** 1000-customer files live directly in the *upstream* `VRPTW/` directory rather than a `VRPTW/GH1000/` subdirectory; the downloader moves them into the *local* `GH1000/` folder. The count of 712 includes only `.vrp` + `.sol` files, excluding accompanying README/license/manifest files.

### Variant categories and naming

All six problem sizes cover categories **C1, C2, R1, R2, RC1, RC2**:

| Class | Placement | Rough scheduling pattern | Common capacity examples (verify per file) |
| --- | --- | --- | ---: |
| C1 | Clustered | Shorter horizon / tighter scheduling | 200 |
| C2 | Clustered | Longer horizon | 700 |
| R1 | Random/dispersed | Shorter horizon | 200 |
| R2 | Random/dispersed | Longer horizon | 1000 |
| RC1 | Mixed clustered/dispersed | Shorter horizon | 200 |
| RC2 | Mixed clustered/dispersed | Longer horizon | 1000 |

- **Solomon:** e.g. `C101.vrp`, `C101.sol`, `R201.vrp`, `RC101.vrp`; **56** total (C1 9, C2 8, R1 12, R2 11, RC1 8, RC2 8).
- **Homberger:** e.g. `C1_2_1.vrp` (200 customers), `R2_4_3.vrp` (400), `RC1_10_10.vrp` (1000). Middle code: `2,4,6,8,10` corresponds to 200,400,600,800,1000. **10 per class × 6 classes × 5 sizes = 300**.
- Types 1/2 differ in **multiple parameters**, including windows, horizon and sometimes capacities. Do not attribute a cost difference solely to window tightness without controlling for other parameters.

### What varies from file to file?

Every problem contains a **single depot**, mandatory customers, synthetic Cartesian XY coordinates, nonnegative demands, customer time windows and vehicle capacity. The fleet cap `VEHICLES` and capacity `CAPACITY` are instance-level constraints. Examples inspected: `C101.vrp` declares **25 vehicles, capacity 200**, while `C1_2_1.vrp` declares **50 vehicles, capacity 200**; values must never be hard-coded. A `DIMENSION: 101` instance has **100 customers plus the depot**. The XY coordinates are **not latitude/longitude** and contain **no street network or traffic history**.

**Do not confuse datasets with routes:** `.vrp` is the problem your algorithm solves; `.sol` is an independently published reference, not a route produced by your algorithm. The 356 pairs give 356 distinct benchmark instances, **not 712 different problems**.

## 4. Actual PyVRP data format, fields and array shapes

The selected repository's input files are **plain-text VRPLIB-format `.vrp`**, converted from the historical Solomon/Homberger `.txt` format by PyVRP. **Do not use the `instance_format="solomon"` loader flag with these `.vrp` files.** The file extensions are real content distinctions: `.vrp` represents the input; `.sol` is a separate route list and reference cost.

### Real `C101.vrp` excerpts (selected rows, not the whole 101-node file)

```text
NAME : C101
TYPE : CVRPTW
DIMENSION : 101
VEHICLES : 25
CAPACITY : 200
SERVICE_TIME : 90
EDGE_WEIGHT_TYPE : EUC_2D
NODE_COORD_SECTION
1 40 50
2 45 68
...
DEMAND_SECTION
1 0
2 10
...
TIME_WINDOW_SECTION
1 0 1236
2 912 967
...
DEPOT_SECTION
1
-1
EOF
```

In the converted `.vrp` files the first column in each section is a **one-based node ID**: the depot is **file ID `1`**, and customers are **file IDs `2..N`**. Python `vrplib.read_instance()` normalizes the `DEPOT_SECTION` to index `0` and arranges the coordinate/demand/window arrays by **zero-based array position** `0..N-1`. Never conflate those two conventions.

| Header / section | Meaning | Data shape after normalization | Important notes |
| --- | --- | --- | --- |
| `NAME` | Benchmark instance name | String | E.g. `C101`, `C1_2_1`; preserve source ID |
| `TYPE` | Routing variant | String | Some files say `CVRPTW`, others `VRPTW`; inspect fields, not just name |
| `DIMENSION` | Total number of nodes including depot | Scalar integer `N` | `n_customers = N - 1` |
| `VEHICLES` | Maximum available vehicles `K` | Scalar integer | Number of **used** routes must be `<= K` |
| `CAPACITY` | Shared vehicle load capacity `Q` | Scalar number | Same capacity within each instance, may vary by instance |
| `SERVICE_TIME` | Fixed customer service duration | **Scalar**, e.g. `90` | Expand to shape `(N,)` for our internal solver, set depot service to `0` |
| `EDGE_WEIGHT_TYPE : EUC_2D` | Euclidean geometry | String | Does **not** itself encode the DIMACS 1-decimal truncation |
| `NODE_COORD_SECTION` | Node XY coordinates | `float[N,2]` | Values are synthetic Cartesian coordinates, **not GPS** |
| `DEMAND_SECTION` | Delivery demands | `float[N]` | Depot demand `0`, no split deliveries |
| `TIME_WINDOW_SECTION` | Permitted service start interval `[a_i,b_i]` | `float[N,2]` | **Present for every selected instance**; early arrival may wait |
| `DEPOT_SECTION` | Depot identifier | One-element integer array (normalized index `0`) | `.vrp` states `1`, followed by `-1` terminator |
| Derived `edge_weight` | Pairwise Euclidean distances | `float[N,N]`, if computed | `vrplib` computes **full-precision** distances for `EUC_2D`, not benchmark-truncated values |

**Service-time subtlety:** `SERVICE_TIME : 90` is a **single constant**, not 101 rows. PyVRP's standardized examples use it for customer service; the depot itself is not a delivery and should have zero service time in our normalized model. Do not mistakenly treat `raw["service_time"]` as already having shape `(N,)`. If later source variants have a `SERVICE_TIME_SECTION`, handle that schema separately and validate its shape.

### `.sol`: reference solution structure and customer indexing

A real reference file for the same problem begins with routes and ends with a cost:

```text
Route #1: 5 3 7 8 10 11 9 6 4 2 1 75
Route #2: 13 17 18 19 15 16 14 12
...
Cost 827.3
```

The solution stores **route visit sequences and a reference total-distance cost**. It does **not** include customer coordinates, demands, windows, arrival times, waiting times or a road graph. Those remain in `.vrp` (or must be computed from a route).

**Indexing trap:** in `C101.sol`, customer label `1` refers to **normalized array index 1**, corresponding to **on-disk `.vrp` node ID 2**. The depot (internal index 0) is implicit at the beginning and end of each route and **is not listed as a customer**. `vrplib.read_solution()` leaves route labels unchanged: do **not** subtract 1 from these labels a second time. Check coverage against the set `{1,...,N-1}`.

### Canonical internal solver data contract

Define one normalized in-memory representation independent of disk indexing. Shape notation: `N=n+1`, `n` mandatory customers, `K` vehicles, `Q` one shared vehicle capacity. This schema is a **design proposal**, not an existing implemented class:

```python
VRPTWInstance(
    name: str,
    family: str,                         # Solomon | GH200 | GH400 | GH600 | GH800 | GH1000
    source_path: str,                    # relative .vrp path
    n_customers: int,
    depot_index: int,                    # always 0 after conversion
    coordinates: array[N, 2],           # x, y for depot and all customers
    demands: array[N],                  # q[0] == 0
    time_windows: array[N, 2],          # service-start interval [a_i, b_i]
    service_durations: array[N],         # 0 at depot; scalar customer time expanded
    max_vehicles: int,                   # K, not number of routes found
    vehicle_capacity: float,            # Q
    distance_matrix: array[N, N],       # optional/lazy; benchmark-specific rounding
    distance_policy: str,               # e.g. cvrlib_dimacs_truncate_1_decimal
    source_commit: str | None,          # pin separately when available
    benchmark_protocol: str,            # see §7
)
```

No default GPS units are implied: XY distances and time windows are **synthetic benchmark units**. The default native benchmark assumes travel time and distance have matching units, but does not provide real-clock timestamps, kilometers or road speed. Always preserve the original `.vrp` and `.sol` unchanged.

## 5. Downloading, folder layout and loading in Python

### Acquisition from the project root

Place [`download_vrptw_benchmarks.py`](download_vrptw_benchmarks.py) in the **EcoRoute-CVRP repository root**, then execute:

```bash
python download_vrptw_benchmarks.py
```

The downloader uses Python's standard library (Python 3.9+) and **does not run `git clone`**. It temporarily downloads the GitHub `main` ZIP from:

```text
https://codeload.github.com/PyVRP/Instances/zip/refs/heads/main
```

It extracts **only** the 356 `.vrp` + 356 `.sol` files in the `VRPTW` collection, verifies six expected folder counts and one-to-one filename pairs, skips unchanged files and discards the ZIP after extraction. It also saves upstream documentation, a license copy and a source manifest. If GitHub later changes the `main` branch, rerunning the script may update files: pin commit and hash files before final benchmark runs.

```text
EcoRoute-CVRP/
├── dataset.md
├── download_vrptw_benchmarks.py
├── data/
│   ├── benchmarks/
│   │   └── vrptw/
│   │       ├── Solomon/           # 56 x (.vrp + .sol) = 112 files
│   │       │   ├── C101.vrp
│   │       │   ├── C101.sol
│   │       │   └── ...
│   │       ├── GH200/             # 60 pairs / 200 customers
│   │       │   ├── C1_2_1.vrp
│   │       │   ├── C1_2_1.sol
│   │       │   └── ...
│   │       ├── GH400/             # 60 pairs / 400 customers
│   │       ├── GH600/             # 60 pairs / 600 customers
│   │       ├── GH800/             # 60 pairs / 800 customers
│   │       ├── GH1000/            # 60 pairs / 1000 customers
│   │       │   ├── C1_10_1.vrp
│   │       │   ├── C1_10_1.sol
│   │       │   └── ...
│   │       ├── UPSTREAM_README.md
│   │       ├── LICENSE
│   │       └── source_manifest.json
│   └── derived/
│       └── traffic/               # future generated TD overlays; NOT in original data
├── tests/
└── results/
```

The actual downloader writes `DESTINATION = Path(__file__).resolve().parent / "data" / "benchmarks" / "vrptw"`: it places data beside the **script's directory**, so keeping the script in the repository root determines the intended destination. Run it from that root for clarity. **It does not make a nested Git repo, `.git` directory, or `PyVRP/Instances/` folder.** The existence of this downloader does not prove the dataset was successfully downloaded in a given checkout; check the files and manifest after execution.

`source_manifest.json` currently records the upstream repo/ZIP URL, download UTC timestamp, archive SHA-256, expected family counts and total instance count. It does **not** pin the upstream commit SHA or record SHA-256 values for each file; capture those as a separate reproducibility step if needed.

### Load `.vrp` and `.sol` using `vrplib`

Install:

```bash
python -m pip install vrplib numpy
```

The following code is for the **selected PyVRP VRPLIB `.vrp` format**, **not** the original Solomon `.txt` format:

```python
from pathlib import Path
import numpy as np
import vrplib

root = Path("data/benchmarks/vrptw")
instance_path = root / "Solomon" / "C101.vrp"
solution_path = root / "Solomon" / "C101.sol"

raw = vrplib.read_instance(str(instance_path))  # default: VRPLIB format
reference = vrplib.read_solution(str(solution_path))

coords = np.asarray(raw["node_coord"], dtype=float)        # (N, 2)
demands = np.asarray(raw["demand"], dtype=float)            # (N,)
windows = np.asarray(raw["time_window"], dtype=float)      # (N, 2)
N = len(coords)
K = int(raw["vehicles"])
Q = float(raw["capacity"])
depots = np.asarray(raw["depot"], dtype=int)              # [0]
assert depots.shape == (1,) and int(depots[0]) == 0

# PyVRP standard examples have scalar SERVICE_TIME, not N separate rows.
service_raw = np.asarray(raw["service_time"], dtype=float)
if service_raw.ndim == 0:
    services = np.full(N, float(service_raw), dtype=float)
    services[0] = 0.0  # the depot is not a delivery
elif service_raw.shape == (N,):
    services = service_raw.copy()  # generic future section-based variant
else:
    raise ValueError(f"Unexpected service_time shape: {service_raw.shape}")

# vrplib's EUC_2D edge_weight is full-precision Euclidean by default.
full_euclidean = np.asarray(raw["edge_weight"], dtype=float)  # (N, N)
# For CVRPLIB/PyVRP's published static reference, use the documented
# truncation-to-one-decimal policy, not full_euclidean as the score.
# Test exact scoring against the published reference route before benchmarking.

assert coords.shape == (N, 2) and N == int(raw["dimension"])
assert demands.shape == (N,) and windows.shape == (N, 2)
assert services.shape == (N,) and full_euclidean.shape == (N, N)
assert N >= 2 and K >= 1 and Q > 0
assert np.all(np.isfinite(coords)) and np.all(np.isfinite(demands))
assert np.all(np.isfinite(windows)) and np.all(np.isfinite(services))
assert np.all(demands >= 0) and demands[0] == 0
assert np.all(services >= 0) and services[0] == 0
assert np.all(windows[:, 0] <= windows[:, 1])
assert np.all(demands[1:] <= Q)

routes = [[int(j) for j in route] for route in reference["routes"]]
assert set(j for route in routes for j in route) == set(range(1, N))
assert sum(map(len, routes)) == N - 1  # no duplicate/missing visits
assert len(routes) <= K
assert all(1 <= j < N for route in routes for j in route)

print(f"{raw['name']}: {N - 1} customers; max K={K}; Q={Q}")
print(f"Reference: {len(routes)} routes; cost={reference['cost']}")
```

The route-coverage assertions **do not prove** that the reference routes meet capacities, scheduling windows, depot deadline or the cost rule. Run the independent validator in §6 and reproduce the reported `.sol` cost with the §7 evaluator before reporting a published comparison. For very large future cases, consider `vrplib.read_instance(..., compute_edge_weights=False)` when you do not need a dense distance matrix (check your installed `vrplib` API); then compute distances on demand instead.

### Shape examples and algorithm inputs

| Input example | `N` | `coordinates` | `demands` | `time_windows` | `service_durations` | Optional dense distances |
| --- | ---: | --- | --- | --- | --- | --- |
| `Solomon/C101.vrp` | 101 | `(101,2)` | `(101,)` | `(101,2)` | `(101,)` after expansion | `(101,101)` |
| `GH200/C1_2_1.vrp` | 201 | `(201,2)` | `(201,)` | `(201,2)` | `(201,)` after expansion | `(201,201)` |
| `GH400/C1_4_1.vrp` | 401 | `(401,2)` | `(401,)` | `(401,2)` | `(401,)` after expansion | `(401,401)` |
| `GH600/C1_6_1.vrp` | 601 | `(601,2)` | `(601,)` | `(601,2)` | `(601,)` after expansion | `(601,601)` |
| `GH800/C1_8_1.vrp` | 801 | `(801,2)` | `(801,)` | `(801,2)` | `(801,)` after expansion | `(801,801)` |
| `GH1000/C1_10_1.vrp` | 1001 | `(1001,2)` | `(1001,)` | `(1001,2)` | `(1001,)` after expansion | `(1001,1001)` |

A feasible solution is **not** a single ordering of all customers; it is a **list of at most `K` routes**, each depot → customers → depot, plus a recomputed schedule. Vehicle load, arrival, service start, waiting, departure and depot return are derived state; they are **not prefilled arrays in the `.vrp` or `.sol` files**.

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

### Protocol A — CVRPLIB / downloaded PyVRP `.sol` references (our **primary** static evaluation)

The selected PyVRP `VRPTW/README.md` explicitly attributes its 356 stored `.sol` BKS to CVRPLIB and states that **distance and duration are truncated to one decimal** (DIMACS convention). For comparisons with these exact `.sol` files:

- Objective: **minimize total traveled distance** subject to VRPTW feasibility, with **at most `K` routes**.
- Edge distance: **Euclidean distance truncated to one decimal place** (not rounded to the nearest tenth). Define `d_ij = floor(10 * hypot(x_i-x_j, y_i-y_j)) / 10` with a carefully tested floating-point policy.
- Solution cost: aggregate distance displayed/rounded to **one decimal** according to the site.
- The downloaded `.sol` contains **published route sequences and their reference `Cost`**, not an exhaustive certificate of optimality. CVRPLIB website columns **`UB`** and **`Opt`** may supply best-feasible costs and proven-optimum flags when independently accessible. **Never infer optimality merely from a `.sol` file.**
- Example: the downloaded `Solomon/C101.sol` reports **827.3** under its convention; this is **not** interchangeable with SINTEF's figure below.

**Agent action:** before batch benchmarking, reconstruct the published cost of `Solomon/C101.sol` and at least one Gehring–Homberger `.sol`, using the normalized solution labels from §4, and test the exact edge-cost policy and numerical tolerance. Treat a mismatch as a blocker, not an “improved” algorithm.

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

The selected raw instance families lack: a real directed road graph, road-segment speed forecasts, hourly time slots, incident closures, live GPS coordinates, and a time-dependent stop-to-stop matrix. **Do not claim any of those exist in the selected `.vrp` files**.

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

- [ ] Archive/source URL is documented; the downloader manifest has the archive SHA-256; **add/pin** upstream Git commit and per-file SHA-256 for the frozen final benchmark snapshot.
- [ ] Instance name, family, class, claimed size, source and **VRPLIB `.vrp` format** are consistent; no accidental use of `instance_format="solomon"`.
- [ ] On disk the `.vrp` has exactly one depot at **file ID `1`**, while parsed arrays have **depot index `0`**; `.sol` customer labels are `1..n` internally. Check all mappings and unique customers.
- [ ] `N = n+1`; coordinates `(N,2)`, demands `(N,)`, windows `(N,2)`; **expand scalar** `SERVICE_TIME` to internal `(N,)` with depot service `0`.
- [ ] All required values finite; `K` positive integer, `Q > 0`, no negative demands or service times, `a_i <= b_i`.
- [ ] Zero depot demand, customer loads `<= Q`; do not treat aggregate `sum(demand) <= K*Q` as sufficient for route feasibility.
- [ ] Temporal horizon/depot due date is meaningful; no time units or time zones invented.
- [ ] Parsed `K`, `Q`, nodes, sample windows and distance costs match selected `.vrp` metadata; `.sol` cost must reproduce under DIMACS truncation.
- [ ] All 356 selected `.vrp` files have exactly one same-stem `.sol`; independently verify multiple published routes and costs under the matching benchmark convention.
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

## 12. Verified source links, scope and provenance

**Chosen primary download source (all 356 `.vrp` + `.sol` pairs):**

1. [PyVRP/Instances GitHub repository](https://github.com/PyVRP/Instances) — complete upstream project; **do not clone everything** for this selected dataset.
2. [PyVRP/Instances — VRPTW collection](https://github.com/PyVRP/Instances/tree/main/VRPTW) and [its README](https://github.com/PyVRP/Instances/blob/main/VRPTW/README.md) — explicitly says original Solomon/Homberger were converted to VRPLIB and stored BKS follow DIMACS 1-decimal truncation.
3. Individual directories: [Solomon](https://github.com/PyVRP/Instances/tree/main/VRPTW/Solomon), [GH200](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH200), [GH400](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH400), [GH600](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH600), [GH800](https://github.com/PyVRP/Instances/tree/main/VRPTW/GH800); [GH1000 is at the VRPTW root](https://github.com/PyVRP/Instances/tree/main/VRPTW).
4. [Exact GitHub archive consumed by the downloader](https://codeload.github.com/PyVRP/Instances/zip/refs/heads/main) — current branch archive (mutable; record SHA-256 and pin a commit for final experiments).
5. [PyVRP/VRPLIB — Python format parser](https://github.com/PyVRP/VRPLIB) — `pip install vrplib`, `vrplib.read_instance('...vrp')`, `vrplib.read_solution('...sol')`; note its README describes the **one-based on-disk depot** → **zero-based parsed index** conversion and the default full-precision Euclidean distances.

**Independent references (not the local source format):**

6. [CVRPLIB — historical VRPTW catalog](https://galgos.inf.puc-rio.br/cvrplib/en/vrptw/instances) — originally cited BKS and optimality flags; site has been inaccessible, so do not make its availability a download prerequisite. Its latest indexed records can be newer than the checked-in `.sol` values.
7. [SINTEF Solomon benchmarks](https://www.sintef.no/projectweb/top/vrptw/100-customers/) and [Gehring–Homberger benchmarks](https://www.sintef.no/projectweb/top/vrptw/homberger-benchmark/) — original Solomon-format `.txt` distributions and a **different**, lexicographic reference protocol. [SINTEF format documentation](https://www.sintef.no/projectweb/top/vrptw/documentation2/).
8. [DIMACS VRPTW challenge](https://dimacs.rutgers.edu/programs/implementation-challenges/vehicle-routing/implementation-challenge-vehicle-routing/vrp-with-time-windows) — benchmark scoring context.
9. [MAMUT-routing](https://github.com/ANR-MAMUT/MAMUT-routing) and [Lera2026 time-dependent family](https://github.com/ANR-MAMUT/MAMUT-routing-TDVRPTW-Lera2026) — **optional separate TD benchmarks**, not included in download.
10. [Original CESI project assignment](https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html) and [`sources.md`](sources.md) — assignment requirements, including at least 20 distinct instances and the expectation of `vrplib`-based reference validation. The separate CESI-provided instance distribution has not been located.

### Outstanding acquisition and research tasks

- [ ] Run the downloader; verify every `NAME.vrp` has `NAME.sol`, and check `source_manifest.json` and license.
- [ ] Record exact source file hashes and Git commit for frozen, reproducible results (the current downloader does not provide per-file hashes/commit SHA).
- [ ] Independently parse at least one case from **each of six local folders** and verify all data shapes and the depot/customer ID conventions.
- [ ] Re-evaluate the published `.sol` route cost under DIMACS truncation and verify its feasibility rather than trusting the stored number blindly.
- [ ] Locate any separately supplied CESI instances if required by tutors; do not conflate them with the public PyVRP files.
- [ ] Choose and version a defensible synthetic or external traffic source; real road data is **not** part of these files.
- [ ] Freeze development, validation and held-out instance IDs, evaluation protocol, parameters, seeds and compute budgets before the final test.

---

**Agent rule:** The purpose of these datasets is to drive a **correct and reproducible advanced VRP solver**, not to induce hidden assumptions from a convenient example. Keep `K`, `Q`, customer attributes, objective, traffic policy, source, and reference conventions explicit at every layer of the implementation.
