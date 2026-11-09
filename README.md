# EcoRoute — Vehicle routing with time windows

EcoRoute studies the **capacitated vehicle routing problem with time windows (CVRPTW)** using the Solomon and Gehring–Homberger benchmark instances. Each route must respect vehicle capacity, customer service windows, and the depot time window. The benchmark objective is **total traveled distance**.

## Repository map

| Path | Purpose |
| --- | --- |
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
