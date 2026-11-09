# EcoRoute — CVRPTW benchmark protocol

## Objective and data

Use the 356 Solomon and Gehring–Homberger VRPTW instances in [`data/benchmarks/vrptw/`](data/benchmarks/vrptw/). Each `.vrp` input has a paired `.sol` published reference solution. The primary objective is **total route distance**, subject to at most `K` vehicles, vehicle capacity `Q`, customer service-start windows, and the depot window. These are static Euclidean benchmark instances.

For comparisons against the bundled `.sol` files, follow the upstream PyVRP/CVRPLIB **DIMACS one-decimal truncation** convention for distance and duration. Reconstruct the published cost of `Solomon/C101.sol` (827.3) and at least one Gehring–Homberger reference before batch evaluation. Resolve any mismatch before reporting gaps. Do not mix these costs with a reference calculated using a different objective, rounding rule, or fleet policy.

## Required evaluation procedure

1. Record each input path, source, file hash, customer count, `K`, `Q`, and reference cost. Keep the source manifest from the downloaded collection.
2. Reserve development instances for algorithm selection and tuning. Freeze at least **20 distinct** held-out instances spanning sizes and customer distributions. Repeated seeds on one instance do not increase the instance count.
3. Define one reproducible run configuration: algorithm version, parameters, time limit, hardware, seed, and evaluation convention.
4. Run a separate validator on every output. Check exactly-once customer coverage, at most `K` routes, capacity, service-start windows, waiting, and depot return. Recompute distance independently.
5. Preserve raw routes, schedules, costs, feasibility result, runtime, seed, logs, and failures for every trial.
6. Report per-instance and aggregate results, including variability across seeds, distance versus runtime, and difficult or failed cases.

The project brief asks for a Python heuristic or metaheuristic, reference comparison, computation time, statistical analysis, and a reproducible demonstration. The existence of this protocol does not mean a benchmark runner or results have been implemented.

## Reference gap

For a feasible result and a **compatible** positive published reference cost `B`:

```text
gap_to_reference_percent = 100 × (our_distance_cost − B) / B
```

Call this a *gap to reference* or *gap to best known* unless the source explicitly proves optimality. A negative gap requires checking the evaluator, route feasibility, and source convention before interpreting it as an improvement. Report route count alongside distance.

## Suggested result record

```text
instance_id, family, n_customers, input_sha256, reference_source,
reference_cost, algorithm_version, seed, time_limit_s, feasible,
vehicles_used, total_distance, gap_to_reference_percent,
runtime_s, solution_path, validation_log_path
```

Use `null` for unknown values rather than inventing a score. The independent validator and its evidence are prerequisites for any published comparison. Data format and customer indexing are documented in [`dataset.md`](dataset.md).


Current modeling contract (2026-11-09): static CVRPTW; minimum total distance; at most K identical-capacity vehicles; hard service-start windows, early waiting, customer service, and a common depot opening/return window. Each active vehicle may choose its depot departure within that same window. Travel duration, waiting and capacity utilization are secondary reported metrics. Traffic and road networks are postponed, and no optimization algorithm is selected or implemented. Algorithm design, splits, runtime budgets and final experiments are future work.


Modeling validation: `main.ipynb` imports the reusable checks in `scripts/cvrptw_model.py`.
Normal mode reports missing collection checks as **NOT RUN** while synthetic examples execute.
For complete validation, run Jupyter from the repository root with `ECOROUTE_STRICT_DATA=1`.
`ECOROUTE_PROJECT_ROOT` and `ECOROUTE_DATA_ROOT` override the project and dataset roots.
No solver, metaheuristic, final dataset split or experimental budget is selected by these checks.
