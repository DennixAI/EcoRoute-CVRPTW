# CVRP implementation plan — independent critical audit

**Audit date:** 2026-11-02  
**Status:** Mathematical modeling notebook exists; full solver and experimental optimization have not yet been implemented.  
**Documents checked:** existing 1,223-line README and 68-cell modeling notebook; current published documentation of PyVRP, HGS-CVRP and VRPLIB.

## Verdict

**Do not start building a single predetermined ALNS architecture without a short comparative prototype.** The mathematical model is a usable draft, but the most important risk is investing significant implementation effort in a metaheuristic whose quality has never been demonstrated on your benchmark mix. A better engineering plan separates correctness, algorithm selection, competitive quality and scale.

## Priority-ranked findings and fixes

1. **CRITICAL — Algorithm choice not proven:** The prior plan favored ALNS. Build both a strong ILS+local-search candidate and an ALNS+local-search candidate; benchmark each on 6–10 development instances with matched objective, fleet and budgets. Use *external* HGS-CVRP and modern PyVRP ILS as independent baselines, not as student-made implementations. Ask the tutor about permitted dependencies and originality first.
2. **CRITICAL — No hard quality target:** Adopt explicit, *provisional* ambitions such as ≤3% mean BKS gap on held-out tests and mandatory investigation of >7% outliers, while disclosing budgets and feasibility. These are targets, **not guarantees** and not grading claims.
3. **CRITICAL — Reference-cost mistakes:** Verify `vrplib` node mapping and per-family distance rounding against published route costs before calculating any gap. Ensure the fleet interpretation matches the reference. Incorrect metrics can produce superficially excellent but invalid gaps.
4. **CRITICAL — Feasible construction is difficult:** Include multiple constructors and capacity-aware repair/route elimination, with explicit failure handling. Heuristic failure cannot prove infeasibility.
5. **HIGH — Strengthen neighborhoods:** Prioritize 2-opt, Or-opt, relocate, swap, 2-opt*, and a serious SWAP* investigation; ALNS removal/greedy/regret repair must be coupled with quality-focused local search.
6. **HIGH — Permit intelligent diversification:** Test calibrated acceptance, perturbations, multi-start, stagnation response, and *optionally* penalized infeasible intermediate solutions while ensuring 100% feasibility of reported outputs.
7. **HIGH — Test invariants aggressively:** Every local move needs exact cost-delta verification against independent full recomputation, including singleton/empty routes, zero demands, equal coordinates, symmetric/asymmetric costs and optional route changes. Never trust merely a passing plotting notebook.
8. **HIGH — Correct factual mislabel:** PyVRP 0.13+ changed to ILS; Vidal's HGS-CVRP is the separate HGS baseline. Comparing “PyVRP HGS” against HGS-CVRP as two HGS solvers would be misleading.
9. **HIGH — Real scalability required:** Show performance at 100, 500, 1,000 and ideally 2,000+ customers with profiles, RAM peaks and measured quality. HGS-CVRP expressly states it was designed up to ~1,000 clients and not directly for >5,000 clients.
10. **HIGH — Limit benchmark overfitting:** Use development vs untouched final test instances, frozen algorithms and full reporting of runs/failures; at least 20 distinct final reference instances remain mandatory.
11. **MEDIUM — Parameter exposure needs discipline:** Variable values belong to instance data and typed solver configuration. Not every theoretical switch should be exposed until it is implemented, tested and documented with units/ranges/defaults and interactions.
12. **MEDIUM — Current model scope boundaries:** At most K vs exactly K and distance vs duration require tutor confirmation; keep time windows/traffic and unsupported vehicle variants out of this CVRP implementation.

## Hard release gates

| Gate | Must demonstrate |
|---|---|
| G1 Data reliability | Round-trip source IDs, preserve depot, demands and distances; reproduce published reference cost |
| G2 Correctness | Every successful solution passes an independent full feasibility and cost auditor |
| G3 Algorithm selection | ILS/ALNS pilot results, external comparisons if allowed, written decision and rationale |
| G4 Quality | Predeclared thresholds, quality-versus-time plots, bad-instance investigation and redesign if weak |
| G5 Scale | Measured runtime, RAM, convergence at increasing n; no invented “supports thousands” claim |
| G6 Evaluation | ≥20 distinct held-out reference instances, repeated seeds, full raw result preservation |
| G7 Defense | Corrected PLNE, choice of heuristic, complexity proof, parameterization, demonstrated reproducibility |

## Specific professor questions to practice

- Why was this heuristic chosen **over ILS, ALNS or HGS**, and where are the paired results?
- Can you prove that all customers are served exactly once, capacities hold and no subtours occur?
- What if a construction algorithm cannot find a feasible set of routes, even though one exists?
- How do you know each move's Δcost and Δload is correct? Does it remain correct for asymmetric arcs?
- What are the exact conventions for `K`, decimal/rounded Euclidean costs, depot labels and BKS status?
- How do you guarantee the algorithm's best output is feasible if it explores temporarily infeasible solutions?
- How do you distinguish *optimal proven*, *best known* and *best found by us*?
- What evidence supports performance on 1,000 or 3,000 customers? How does memory scale?
- Why do separate seeds, reproducible budgets, and disjoint tuning/test sets matter?
- Why is total **distance** the objective when ADEME's scenario described travel **duration**?

## Immediate priority order

1. Obtain critical tutor scope/originality approvals and confirm benchmark rules.
2. Implement and stress-test canonical data loader + independent route evaluator.
3. Lock 6–10 development instances and ≥20 *separate* final-test instances.
4. Implement reliable feasible construction and strong local search with randomized delta tests.
5. Pilot ALNS and ILS; compare with version-pinned HGS/PyVRP where permitted; select architecture.
6. Implement chosen metaheuristic, strength improvements and acceleration based on measured bottlenecks.
7. Tune **only on development instances**, lock the final protocol, then benchmark, interpret and deliver.

### Corrections applied to the master README

The updated `README.md` now includes a new **§17** giving algorithm-selection experiments, explicit quality gates, contingency actions, neighborhood specifications, reference auditing and extra professor checks. The incorrect identification of modern PyVRP as HGS has been corrected.

### Sources

- PyVRP release notes: https://github.com/PyVRP/PyVRP/releases
- PyVRP algorithm: https://pyvrp.org/notebooks/pyvrp_implementation.html
- PyVRP benchmark protocol: https://pyvrp.org/dev/benchmarking.html
- HGS-CVRP: https://github.com/vidalt/HGS-CVRP
- VRPLIB: https://github.com/PyVRP/VRPLIB
