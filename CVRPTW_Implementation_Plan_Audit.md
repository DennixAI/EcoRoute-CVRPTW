# CVRPTW implementation review

## Current assessment

The repository contains a static CVRPTW modeling notebook, a downloaded benchmark collection, and documentation. It does not yet establish a complete standalone optimization solver or a reproducible evaluation campaign. Model examples and reference-route plots should not be presented as algorithm results.

## Priority checks

| Priority | Check | Evidence needed |
| --- | --- | --- |
| 1 | Data and indexing | Parse every selected `.vrp`; map depot and customer IDs correctly; reject invalid input |
| 2 | Independent feasibility | Verify exactly-once coverage, route count, capacity, waiting, service starts, and depot return |
| 3 | Reference scoring | Reproduce published `.sol` costs under the declared one-decimal distance convention |
| 4 | Solver choice | Compare candidate methods on the same development instances, objectives, seeds, and time budgets |
| 5 | Evaluation | Freeze at least 20 distinct held-out instances; preserve all runs and failures |
| 6 | Reporting | Show distance, vehicles, gap to a compatible reference, runtime, variability, and limitations |

## Modeling cautions

- A feasible route must respect both capacity and time windows; checking customer coverage alone is insufficient.
- Early arrival permits waiting. Service must start within the customer's window; return must respect the depot window.
- Static distance and schedule calculations must use the benchmark's stated precision rules.
- Published `.sol` routes are references, not outputs from our solver and not automatically proven optima.
- A heuristic failing to find a route does not prove the instance infeasible.
- An incremental move evaluator should be checked against full independent recomputation, including schedule changes after an insertion or swap.

## Release gates

A result is ready for the final report only when its input and source hash are recorded, its solution passes the independent validator, its cost is recomputed under the selected protocol, and its runtime and random seed are saved. Report failed runs as failures. Compare only like-for-like benchmark costs. See [`dataset.md`](dataset.md) and [`benchmarks.md`](benchmarks.md) for the data and reporting contracts.
