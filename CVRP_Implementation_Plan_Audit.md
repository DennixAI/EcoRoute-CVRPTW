# CVRP implementation plan — independent critical audit

## Advanced reassessment — 2026-11-07

### PR 1 mathematical review corrections

The follow-up review corrected the specification, not the untouched notebook or an implemented solver:

- **FIFO schedule dominance:** for fixed route and depot departure, earliest service minimizes return and elapsed time. Extra customer holding cannot improve that primary objective. Flexible depot departure still needs optimization (context A2).
- **Grid semantics:** define tick conversion explicitly, avoid demand/capacity rounding, and supply completion-window equation D3c. A grid trajectory must be replayed with original service/travel times; copied grid departure times need not satisfy the continuous no-post-service-holding policy (A4).
- **Certificates:** grid infeasibility and grid lower bounds do not certify the continuous problem. The continuous replay cost and the discrete objective are separate values (A4).
- **Complexity:** use metric TSP with costs in {1,2}, keeping the horizon and explicit travel table polynomial in the reduction input size; scope decision NP-completeness to that explicit finite-table variant (A4).
- **Activation and symmetry:** exactly-K fixes every z to one; optional truck-label symmetry requires identical temporal and cost parameters, not only equal capacities (A2/A4).
- **Benchmark ordering:** hierarchical fleet/distance results require lexicographic comparison; a distance gap is conditional on matching fleet count and conventions (A6).
- **Implementation instructions:** remove active assumptions that A0 has selected ALNS, and replace static-only move evaluation instructions with advanced schedule propagation where required (README).

Validation for this documentation correction includes small enumerated FIFO schedule/grid-replay checks, preservation of the French archive and historical prompts, unchanged notebook/animation bytes, Markdown link/fence checks and whitespace review. These checks support the stated examples and internal consistency; they are not solver benchmarks, a general implementation verification or tutor approval.

The earlier audit below is preserved as a **historical classical-CVRP audit dated 2026-11-02**. Its instruction to exclude windows/traffic is superseded by the user's explicit TD-CVRPTW decision. Apply its algorithm-quality principles to the new three-layer specification in [context A1–A8](context.md#a1-scope-and-authority) and the synchronized [README](README.md). Classical performance ambitions and HGS-CVRP comparisons remain Layer 1 only.

### Findings against the advanced target

| Priority | Risk / previous limitation | Required correction and evidence |
|---|---|---|
| Critical | Static distance objectives do not define traffic-aware tour duration | Proposed sum of active return minus departure; driving/waiting/service/makespan/distance separately reported; tutor acceptance pending |
| Critical | No customer temporal state in the existing notebook | Define arrival/start/completion/departure/wait, service-start versus completion policy and depot limits; inactive schedules zero (context A2) |
| Critical | A fixed matrix cannot represent road forecasts | Integrated segment speeds across intervals plus FIFO time-dependent paths, provenance and horizon checks; no real forecast dataset bundled (A3) |
| Critical | Nonlinear travel expression mislabeled MILP would invalidate exact claims | Explicit time-indexed D1–D6 reference formulation, exact only for its grid; preserve MTZ and continuously revalidate (A4) |
| Critical | Static move deltas miss cascading timing changes | Recompute affected schedules/paths; validate incremental state against independent full evaluator; flexible departure may require full rescheduling |
| Critical | Published CVRP/VRPTW values use different objectives | Separate categories A/B/C; SINTEF Solomon fleet-then-distance values are not elapsed-time optima; no fabricated advanced gap |
| High | ALNS selected without comparative evidence | Keep A0: own time-aware ALNS versus ILS; investigate tabu/hybrids with matched data/budgets and repeated seeds; external solver support verified per constraint |
| High | Feasible construction may fail with tight windows | Time-feasible insertions, service/traffic-aware regret repair, multiple starts and explicit failure; never infer proof from failed search |
| High | Large temporal tables and suffix propagation threaten scaling | O(K n² h) exact size; bounded caches, road-profile storage, candidates and profiling; no unmeasured thousands-customer claims |
| High | Notebook filenames and repository status were stale | Actual sole notebook is `CesiCDP_CVRP_Modeling.ipynb`; 68 cells/19 PNGs/no saved errors; repository exists; absent historical artifacts are listed in A8 |
| High | Documentation could be mistaken for implementation | Advanced notebook, solver, experiments and tutor approval remain pending; notebook unchanged in this task |

### Updated release gates

1. Review temporal objective, fleet rule, window semantics, departure/holding and finite horizon with tutor.
2. Update the actual modeling notebook in the next phase; validate Layers 1/2/3 and tiny exact grid cases.
3. Implement validated instance/forecast schemas and independent continuous route-schedule auditor; reject missing data and unsupported closures.
4. Test waiting, service, interval crossings, FIFO, path switches, return limits, activation and zero-demand/zero-time cases.
5. Compare ALNS/ILS development pilots using complete temporal evaluation; require validated feasible incumbents and raw failures.
6. Freeze ≥20 distinct final instances under the proposed 8 CVRP/6 CVRPTW/6 TD-CVRPTW allocation, subject to tutor agreement. Keep the historical ≥20 classical-reference ambition as an optional larger campaign, not an official category quota.
7. Report all temporal metrics, objective-compatible references, runtime/RAM/robustness, sensitivity and figures with scientific questions; prepare reproducible notebook and English defense.

No gate is satisfied merely by documenting it. The original audit's ≤3% mean BKS gap and >7% diagnosis trigger are provisional classical distance targets; advanced targets must be defined with comparable baselines and development evidence. The advanced configuration contract, data policies, test cases and ownership questions are specified in context A5–A8.

### Research boundary

The original CESI page could not be retrieved on 2026-11-07; use the preserved statement in [sources.md](sources.md). The reviewed SINTEF benchmark page supplies the static VRPTW objective caveat. Ichoua–Gendreau–Potvin supplies the traffic modeling research basis. See [dated research notes](sources.md#3-advanced-scope-research-notes-2026-11-07). No third-party departure-time-dependent traffic solver or installed version is established by this audit.

## Historical audit — 2026-11-02

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
