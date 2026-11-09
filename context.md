# EcoRoute — CVRPTW project context

## Scope

The project addresses **capacitated vehicle routing with time windows (CVRPTW)**. The supplied Solomon and Gehring–Homberger instances contain customer locations, demands, service durations, vehicle limits, and hard time windows. The benchmark objective is to minimize total traveled distance while respecting all constraints. This document describes the current model and planned implementation; it does not claim that a finished solver or measured results exist.

## Mathematical model

Let `V = {0, 1, ..., n}` contain depot `0` and all customers. Each customer `i` has demand `q_i`, service duration `s_i`, and service-start window `[e_i, l_i]`. Each vehicle has capacity `Q`; at most `K` vehicles may be used. Travel distance and duration between nodes are static and follow the selected benchmark convention.

A feasible route starts at the depot, visits distinct customers, and returns to the depot. Every customer appears on exactly one route. The sum of demands on each route is at most `Q`. For consecutive visits `i, j`, the service start at `j` is at least the service start at `i` plus service duration at `i` and travel duration `i → j`; early arrivals may wait. Service starts within each customer window, and the vehicle returns within the depot window. Inactive vehicles have no route.

The objective is the sum of all traveled arc distances. A mixed-integer formulation can use arc-selection variables, vehicle activation, load propagation or subtour elimination, and temporal precedence constraints. Any proposed linearization must have valid bounds. The [`main.ipynb`](main.ipynb) notebook is the current modeling artifact; its claims should be checked against the actual code before implementation work.

## Data and reference conventions

The repository contains 56 Solomon and 300 Gehring–Homberger instances in [`benchmarks/vrptw/`](benchmarks/vrptw/), each with a `.vrp` input and `.sol` published reference route. The files are PyVRP-converted VRPLIB format. On disk, `.vrp` node IDs start at `1` for the depot; `.sol` customer labels use `1..n`, matching normalized customer indices when the depot is index `0`. Keep the input data and published solutions distinct from results produced by our algorithm.

The bundled reference costs use the PyVRP/CVRPLIB one-decimal truncation convention. Recompute a published route's feasibility and cost before using its cost as a benchmark. A `.sol` cost is a published reference, not proof of optimality. See [`dataset.md`](dataset.md) and [`benchmarks.md`](benchmarks.md).

## Implementation priorities

1. Validate input fields, node indexing, fleet limit, capacity, service windows, and depot return.
2. Build an independent route and cost evaluator and reproduce representative published `.sol` costs.
3. Implement and compare feasible solution methods on development instances; keep random seeds and budgets fixed for fair comparison.
4. Freeze at least 20 distinct held-out instances, run repeated trials, and preserve every result and failure.
5. Report feasibility, distance, route count, gap to a compatible reference, runtime, variability, and limitations.

The notebook and docs establish a starting point. They do not substitute for an implemented solver, automated checks, or reproducible experiments.
