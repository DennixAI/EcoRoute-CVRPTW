# EcoRoute — Vehicle routing with time windows

EcoRoute studies the **capacitated vehicle routing problem with time windows (CVRPTW)** using the Solomon and Gehring–Homberger benchmark instances. Each route must respect vehicle capacity, customer service windows, and the depot time window. The benchmark objective is **total traveled distance**.

## Setup and run order

Run the commands below from the repository root. The project currently performs mathematical modeling and supplied-route validation; no optimization algorithm is selected or implemented.

### 1. Create an isolated Python environment

Use Python 3.9–3.12. Validation was performed with Python 3.9.6; other versions in this range have not yet been tested. On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, create it with `py -m venv .venv`, then activate with `.venv\Scripts\Activate.ps1` in PowerShell before the two `python -m pip` commands. [requirements.txt](requirements.txt) pins the direct dependencies from the tested environment; it is not a complete transitive lockfile.

### 2. Obtain data only if missing

The collection is already included at `data/benchmarks/vrptw/`. Skip this step when those files exist. To download or deliberately refresh the collection:

```bash
python scripts/download_vrptw_benchmarks.py
```

This downloads the selected 356 problem/reference pairs and records archive provenance. Refreshing from upstream can change data; preserve hashes for reproducible experiments.

### 3. Run the complete modeling validation

```bash
python scripts/run_modeling.py --strict
```

The runner executes every cell of `main.ipynb` in a fresh kernel using the active Python environment. Strict mode checks all 356 reference pairs and fails on missing data, invalid routes or mismatched costs. A successful run writes `outputs/main.executed.ipynb`; open that notebook in VS Code or another notebook viewer to inspect the tables and plots. The source `main.ipynb` is not overwritten.

To run synthetic modeling examples when the collection is unavailable:

```bash
python scripts/run_modeling.py
```

Missing collection-dependent checks are explicitly marked **NOT RUN**. Present but invalid benchmark data still fail. You may change the data/output locations:

```bash
python scripts/run_modeling.py --strict --data-root /path/to/vrptw --output outputs/review.ipynb
python scripts/run_modeling.py --help
```

For interactive editing, open `main.ipynb` in your notebook editor, select `.venv` as the kernel, and use **Restart Kernel → Run All**. This requirements file supplies the execution kernel, not a browser-based Jupyter interface. Use the runner above if you only need execution and saved results.

### What each script does

| File | Run directly? | Purpose |
| --- | --- | --- |
| `scripts/download_vrptw_benchmarks.py` | Only if data are missing or a refresh is intended | Acquires the selected benchmark files |
| `scripts/run_modeling.py` | Yes, after dependency installation | Executes and validates the notebook |
| `scripts/cvrptw_model.py` | No | Reusable parsing, schedule and equation checks imported by the notebook |

No temporary `/private/tmp/` review scripts are required. Algorithm selection, optimization runs, tuning and final experiments remain future work.

## Repository map

| Path | Purpose |
| --- | --- |
| [`requirements.txt`](requirements.txt) | Pinned direct modeling/execution dependencies |
| [`scripts/run_modeling.py`](scripts/run_modeling.py) | Fresh-kernel notebook execution |
| [`main.ipynb`](main.ipynb) | Mathematical modeling, examples, plots, and reference-route validation |
| [`data/benchmarks/vrptw/`](data/benchmarks/vrptw/) | 356 `.vrp` instances with 356 paired `.sol` reference solutions |
| [`scripts/download_vrptw_benchmarks.py`](scripts/download_vrptw_benchmarks.py) | Downloads the benchmark collection |
| [`dataset.md`](dataset.md) | Data format, indexing, and acquisition rules |
| [`benchmarks.md`](benchmarks.md) | Evaluation protocol and reporting checklist |
| [`context.md`](context.md) | Model assumptions and project status |

## Problem definition

An instance supplies a depot, customers, coordinates, demands, vehicle capacity `Q`, maximum available vehicles `K`, service durations, and time windows. A feasible solution serves each customer exactly once, uses at most `K` routes, never exceeds `Q` on a route, and completes every route within the depot window. A vehicle may arrive early and wait; customer service must **start** within the customer's window.

The benchmark files use static Euclidean travel. For the bundled PyVRP/CVRPLIB reference solutions, distances and travel durations follow the source's **one-decimal truncation** convention. Compare results only after reproducing the published reference cost with the same convention.

## Get the data

The benchmark collection is checked into `data/benchmarks/vrptw/`. To download it again from PyVRP/Instances, run from the repository root:

```bash
python scripts/download_vrptw_benchmarks.py
```

The script writes to `data/benchmarks/vrptw/` regardless of the shell's current directory. It downloads only the VRPTW collection, checks the six expected family counts and matching problem/solution files, and writes a source manifest. Rerunning it may refresh the manifest and files if the upstream archive changes; freeze hashes before final experiments.

For Python parsing, install `vrplib` and use its default VRPLIB reader for the supplied `.vrp` files. See [`dataset.md`](dataset.md) for indexing and a loading example.

## Current status

The notebook contains a mathematical model and validation examples. A complete standalone optimization solver, independent benchmark runner, and final experimental results are **not established by the files in this repository**. Treat proposed algorithms and measurements as future work until reproducible code and run artifacts exist.

## Evaluation target

The project brief calls for a Python heuristic or metaheuristic, at least **20 distinct problem instances**, comparison against compatible reference solutions, computation time, statistical analysis, and a reproducible final presentation. Use separate development and held-out evaluation instances. For each final run, verify feasibility independently, record the route count and distance, and compute the percentage gap only against a reference using the same objective and distance convention. See [`benchmarks.md`](benchmarks.md).


Current modeling contract (2026-11-09): static CVRPTW; minimum total distance; at most K identical-capacity vehicles; hard service-start windows, early waiting, customer service, and a common depot opening/return window. Each active vehicle may choose its depot departure within that same window. Travel duration, waiting and capacity utilization are secondary reported metrics. Traffic and road networks are postponed, and no optimization algorithm is selected or implemented. Algorithm design, splits, runtime budgets and final experiments are future work.


Modeling validation: `main.ipynb` imports the reusable checks in `scripts/cvrptw_model.py`.
Normal mode reports missing collection checks as **NOT RUN** while synthetic examples execute.
For complete validation, run Jupyter from the repository root with `ECOROUTE_STRICT_DATA=1`.
`ECOROUTE_PROJECT_ROOT` and `ECOROUTE_DATA_ROOT` override the project and dataset roots.
No solver, metaheuristic, final dataset split or experimental budget is selected by these checks.
