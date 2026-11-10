# EcoRoute — Vehicle routing with time windows

> Authoritative project handbooks: [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md). They preserve the assignment and dataset details, distinguish original requirements from our static CVRPTW scope, and define candidate algorithms, worktrees, persistent benchmark results, engineering targets and unresolved decisions. Use them for current project instructions; no algorithm has been selected or implemented.

EcoRoute studies the **capacitated vehicle routing problem with time windows (CVRPTW)** using the Solomon and Gehring–Homberger benchmark instances. Each route must respect vehicle capacity, customer service windows, and the depot time window. The benchmark objective is **total traveled distance**.

## Setup and run order

Run the commands below from the repository root. The project performs mathematical modeling and supplied-route validation. Algorithm 1 (ALNS + VND) is implemented and benchmarked: see [docs/alns_vnd.md](docs/alns_vnd.md) and [results/alns-vnd/README.md](results/alns-vnd/README.md). No final method is selected.

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
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Authoritative scope, assignment, datasets, mathematical contract and benchmarking workflow |
| [`scripts/benchmark.py`](scripts/benchmark.py) | Shared solver interface, independent scoring, persistent campaigns and comparisons |
| [`scripts/run_benchmarks.py`](scripts/run_benchmarks.py) | Replay references or evaluate saved external routes |
| [`scripts/verify_dataset.py`](scripts/verify_dataset.py) | Complete 356-pair verification with durable evidence |
| [`tests/`](tests/) | Automated unit/integration regressions |

## Problem definition

An instance supplies a depot, customers, coordinates, demands, vehicle capacity `Q`, maximum available vehicles `K`, service durations, and time windows. A feasible solution serves each customer exactly once, uses at most `K` routes, never exceeds `Q` on a route, and completes every route within the depot window. A vehicle may arrive early and wait; customer service must **start** within the customer's window.

The benchmark files use static Euclidean travel. For the bundled PyVRP/CVRPLIB reference solutions, distances and travel durations follow the source's **one-decimal truncation** convention. Compare results only after reproducing the published reference cost with the same convention.

## Get the data

The benchmark collection is checked into `data/benchmarks/vrptw/`. To download it again from PyVRP/Instances, run from the repository root:

```bash
python scripts/download_vrptw_benchmarks.py
```

The script writes to `data/benchmarks/vrptw/` regardless of the shell's current directory. It downloads only the VRPTW collection, checks the six expected family counts and matching problem/solution files, and writes a source manifest. Rerunning it may refresh the manifest and files if the upstream archive changes; freeze hashes before final experiments.

For Python parsing, install `vrplib` and use its default VRPLIB reader for the supplied `.vrp` files. See [AGENTS.md](AGENTS.md) §4 and §9 for indexing, the shared input interface and evaluation commands.

## Current status

The notebook contains a mathematical model and validation examples. The shared dataset/benchmark evaluator and automated tests exist. An optimization solver and final algorithm experimental results have not been implemented. Treat proposed algorithms and measurements as future work until reproducible code and run artifacts exist.

## Evaluation target

The project brief calls for a Python heuristic or metaheuristic, at least **20 distinct problem instances**, comparison against compatible reference solutions, computation time, statistical analysis, and a reproducible final presentation. Use separate development and held-out evaluation instances. For each final run, verify feasibility independently, record the route count and distance, and compute the percentage gap only against a reference using the same objective and distance convention. See [AGENTS.md](AGENTS.md) §7 and §9.


Current modeling contract (2026-11-09): static CVRPTW; minimum total distance; at most K identical-capacity vehicles; hard service-start windows, early waiting, customer service, and a common depot opening/return window. Each active vehicle may choose its depot departure within that same window. Travel duration, waiting and capacity utilization are secondary reported metrics. Traffic and road networks are excluded from the selected scope, and no optimization algorithm is selected or implemented. Algorithm design, splits, runtime budgets and final experiments are future work.


Modeling validation: `main.ipynb` imports the reusable checks in `scripts/cvrptw_model.py`.
Normal mode reports missing collection checks as **NOT RUN** while synthetic examples execute.
For complete validation, run Jupyter from the repository root with `ECOROUTE_STRICT_DATA=1`.
`ECOROUTE_PROJECT_ROOT` and `ECOROUTE_DATA_ROOT` override the project and dataset roots.
No solver, metaheuristic, final dataset split or experimental budget is selected by these checks.


## 4. Verify the infrastructure and evaluate supplied routes

After setup, run tests, then save a fresh full-collection report and a reference replay campaign. Choose new output directory names on reruns; no earlier campaign is overwritten:

```bash
python -m unittest discover -v
python scripts/verify_dataset.py --output reports/verification/my-verification
python scripts/run_benchmarks.py --reference-fixture --output results/my-reference-fixture
```

The fixture evaluates **20 distinct test instances × two seeds**, plus one disjoint development fixture × two seeds. It reuses published routes to test scoring/persistence; it does not run or select a routing algorithm. C101 must score **827.3**. Supplied references are best-known solutions, not proven optima, under the [source collection's DIMACS convention](https://github.com/PyVRP/Instances/tree/main/VRPTW). A zero replay gap is expected and is not solver-quality evidence. Solver execution time stays null.

For saved external outputs:

```bash
python scripts/run_benchmarks.py --manifest /path/to/campaign.json --output results/my-external-evaluation
```

[AGENTS.md](AGENTS.md) §9 contains the exact JSON manifest format and Python adapter API. Each declared variant/instance/seed attempt is retained, including missing/invalid/error/timeout cases. CSV/JSON/Markdown tables, plots, schedules, route artifacts, hashes, versions and hardware metadata persist under the new campaign directory. Gap is `100 * (independently_validated_cost - verified_reference_cost) / verified_reference_cost`; invalid routes or references have no eligible gap. Imports cannot establish measured solver runtimes or algorithm PASS. Candidate algorithms remain unimplemented.

Default engineering targets are average gap ≤3%, ≥20 held-out instances with repeated seeds, 100% feasible planned outputs and investigation of any individual gap >7%. Campaign reports show explicit PASS / NEEDS IMPROVEMENT with reasons; final runtime/memory budgets and tutor scope approval remain pending. Preserve these results in Git or a durable archive before long experiments; `outputs/` is only notebook scratch space. The user removed the older context/dataset/benchmarks documents; their requirements are preserved in both synchronized handbooks.

## Live benchmark viewer (including Claude worktrees)

With the project environment activated, open a continuously updating Matplotlib window:

```bash
python scripts/watch_benchmarks.py
```

By default it finds the newest solver campaign across registered Git worktrees at startup.
To watch Claude's specific campaign explicitly:

```bash
python scripts/watch_benchmarks.py \
  --campaign /Users/denni/EcoRoute-CVRPTW/.claude/worktrees/cvrptw-alns-vnd-4fa707/results/alns-vnd/test-001 \
  --interval 3
```

The viewer polls completed `result.json` artifacts, including parallel `shards/`, every
three seconds and redraws when results change. It shows finished/total runs, percentage complete, remaining runs, fully completed
instances, a rough ETA from observed campaign throughput, and the running equal-weight
mean of available instance means, per-instance mean/min/max gaps, execution time by size,
and seed coverage. The ETA includes parallel execution in the observed throughput,
but varying instance sizes or stalled workers can change it substantially; it is not
a guaranteed finish time. Counts describe recorded attempts, including failed runs,
and refresh every poll; the ETA display refreshes at least every 30 seconds. Pending, infeasible and unscored runs remain visible; known scoring,
reference, timeout and budget problems are flagged. It uses the recorded independent
evaluator outputs; it does not revalidate routes or run the solver. Partial feasible-only
statistics cannot establish a final PASS. BKS gaps do not establish proven optimality.
Merged copies are deduplicated by run ID. If there are retries, the latest attempt per
planned variant/instance/seed is plotted and the additional attempt count is displayed.

The viewer reads the observed campaign without modifying it or switching Git branches.
It stays on the selected campaign until closed. Close the plot window or press Ctrl+C
to stop. Add `--save outputs/live-benchmarks.png` to update a PNG outside the observed
campaign whenever new results arrive. An interactive Matplotlib backend is required;
on macOS, if needed, use `MPLBACKEND=MacOSX python scripts/watch_benchmarks.py`.
This viewer needs no additional dependencies beyond `requirements.txt`.

## Algorithm 1 — ALNS + VND

```bash
python -m pip install -r algorithms/alns_vnd/requirements.txt   # adds numba, psutil
python -m unittest discover                                      # full test suite
python scripts/run_alns.py run --split-file results/alns-vnd/split.json --split test \
    --seeds 0 1 2 3 4 5 6 7 8 9 --time-per-customer 0.3 --workers 6 --output results/alns-vnd/<new-id>
```

Held-out result (`test-001`): 360/360 feasible, mean gap 0.654 % to published BKS, worst run 2.364 %. Details in [results/alns-vnd/README.md](results/alns-vnd/README.md).

**Source of truth:** the ALNS + VND solver code lives in `main.ipynb` (Sections 12–15, cells headed `%%alns_source`). `algorithms/alns_vnd/*.py` are identical copies kept because Numba caches compiled code only for real files (instant notebook start) and isolated benchmark workers import files. After editing solver cells run `python scripts/sync_notebook_solver.py --write`; `tests/test_notebook_solver.py` fails while they differ, and the notebook compiles its own cells (with a warning) until then.
