# CesiCDP — CVRP Optimization Project

> **Living project README / execution plan**  
> **Scope:** basic Capacitated Vehicle Routing Problem (CVRP, Level B), not CVRPTW.  
> **Document updated:** 2026-11-02.  
> **Project status:** modeling notebook drafted; tutor approval outstanding; optimization solver and final experiments **not started**.  
> **Rule:** change instance values and algorithm settings through data/configuration, **never by editing core equations or hard-coding a particular benchmark**.

## Contents

> **Audit update (2026-11-02):** The implementation strategy was critically reviewed. A mandatory algorithm-selection gate, hard performance targets, stronger neighborhoods, benchmark validity policies, and contingency triggers have been added in §17. The optimizer is **not** built or validated.

1. [Executive status, non-negotiable requirements, and scope](#1-executive-status-non-negotiable-requirements-and-scope)
2. [What exists today: evidence and limitations](#2-what-exists-today-evidence-and-limitations)
3. [Decisions and approvals required](#3-decisions-and-approvals-required)
4. [Master configurable parameter register](#4-master-configurable-parameter-register)
5. [Mathematical model and formal validation checklist](#5-mathematical-model-and-formal-validation-checklist)
6. [Full work breakdown and ordered TODOs](#6-full-work-breakdown-and-ordered-todos)
7. [Algorithm strategy: maximize solution quality](#7-algorithm-strategy-maximize-solution-quality)
8. [Benchmark design and statistical analysis](#8-benchmark-design-and-statistical-analysis)
9. [Testing, correctness, and acceptance criteria](#9-testing-correctness-and-acceptance-criteria)
10. [Anticipated tutor/professor questions](#10-anticipated-tutorprofessor-questions)
11. [Reproducibility, interfaces, and project structure](#11-reproducibility-interfaces-and-project-structure)
12. [Risk management and contingency plans](#12-risk-management-and-contingency-plans)
13. [Ownership, review workflow, and deadlines](#13-ownership-review-workflow-and-deadlines)
14. [Deliverable checklists](#14-deliverable-checklists)
15. [References and research tasks](#15-references-and-research-tasks)
16. [Immediate next actions and decision log](#16-immediate-next-actions-and-decision-log)
17. [Critical algorithm-quality audit and implementation gates](#17-critical-algorithm-quality-audit-and-implementation-gates)

**Checkbox legend**

- `[x]`: artifact/evidence already present and inspected; not automatically a professor-approved result.
- `[ ]`: not completed, not independently established, or still requires review.
- **`[APPROVAL — USER]`**: the team lead/user must decide or explicitly accept the assumption.
- **`[APPROVAL — TUTOR]`**: the teacher/tutor must validate it.
- **`[RESEARCH]`**: verify against a scientific paper, official benchmark convention, current library documentation, or the assessment brief.
- **`[BLOCKER]`**: do not label the dependent milestone “done” until resolved.
- **`[OPTIONAL]`**: not required for the basic CVRP deliverable; include only if approved and time permits.

---

## 1. Executive status, non-negotiable requirements, and scope

### 1.1 Exact current status

| Workstream | Status | Evidence | Remaining gate |
|---|---|---|---|
| Mathematical formulation | **Draft done** | `CesiCDP_CVRP_Detailed_Modeling.ipynb` | Formal tutor review and corrections |
| Reusable synthetic data | **Demonstrated** | Notebook generator/configuration, plots | Generality and edge-case review |
| Real VRPLIB data example | **Demonstrated on one instance** | Embedded A-n32-k5 and published route/cost 784 | Verify selected families and rounding for every later instance |
| Route feasibility checking | **Demonstrated** | Handwritten and published reference route checks | Standalone independently tested validator for the solver |
| Exact ILP solver | **Not implemented** | Equations only | Optional small-instance benchmark; request approval |
| Route construction algorithm | **Not implemented** | None | Design, implement, test |
| Local search | **Not implemented** | None | Design, implement, test |
| Main metaheuristic | **Not implemented** | None | Compare strategies, choose and implement |
| 20+ instance experimental evaluation | **Not started** | Only one modeling demonstration exists | Prepare dataset manifest, run controlled experiments |
| Statistical analysis of **solver** performance | **Not started** | Modeling charts are not solver results | Execute repeated optimization runs and analyze |
| Final consolidated notebook | **Not started** | First-checkpoint notebook exists | Integrate validated model + algorithm + results |
| English oral defense | **Not started** | No deck/demo/rehearsal | Prepare in final stage |

> **Truthfulness standard:** 19 plots demonstrating *input data, reference routes, mathematical constraints and model size* are **not** evidence of having optimized 19 instances. The published A-n32-k5 solution with cost 784 was **loaded and checked**, not found by our algorithm. Do not claim an achieved gap, solved instance count, performance gain, or optimality without actual experimental evidence.

### 1.2 Requirements taken from the project brief

- [x] Restrict the current implementation to **Level B CVRP**: one depot, homogeneous-capacity trucks, capacity constraints, routes that return to the depot.
- [ ] Create a Python solver for realistically large instances, with an ambition to handle **several thousand customers**; separately report sizes actually tested.
- [ ] Implement and explain a **metaheuristic** (e.g., ALNS, tabu search, simulated annealing, hybrid genetic search), not just call a black-box benchmark solution.
- [ ] Provide a **corrected complete ILP/PLNE**, decision variables, objective, all constraints, complexity argument, and explain any exact-solver role.
- [ ] Demonstrate algorithm flow: initialization, iterations, neighborhoods, adaptation/acceptance, termination, solution extraction.
- [ ] Evaluate **at least 20 distinct problem instances** across varied scenarios; repeated seeds do **not** count as additional distinct instances.
- [ ] Use the Python **`vrplib`** library to load official reference-format instances.
- [ ] Compare to appropriate **best-known solutions (BKS)** or **proven optimal solutions** with the same cost metric.
- [ ] Calculate gap (%) and clearly label whether the reference is proven optimal or only best known.
- [ ] Measure quality, runtime, scalability, robustness, and parameter sensitivity with descriptive statistics and informative plots.
- [ ] Explain strengths, weaknesses, failure modes, and justified improvements.
- [ ] Prepare readable, commented, performant Python in a storytelling-oriented notebook/script with reproducible tests and figures.
- [ ] Prepare an **English** progress/results presentation and a **short executable demo** with a schedule of done/in-progress/next tasks.
- [ ] Record tutor feedback after the first modeling checkpoint; incorporate revisions before final submission.
- [ ] Follow up on the brief's note that a gap above roughly **7–10% may cap the grade at B**; it is a grading warning, **not** a guarantee of a specific grade below the threshold.

### 1.3 In-scope / out-of-scope contract

**IN basic CVRP:** selected customers are all mandatory; one depot; at most or exactly `K` identical-capacity trucks (decision pending); nonnegative, known demands; each customer assigned to exactly one route; no split deliveries; start/end at depot; static distance costs for VRPLIB comparisons; possibly asymmetric precomputed costs *if the loaded dataset supports them*; any valid number of clients, routes, and per-instance capacity; configurable construction/search settings.

**NOT IN current mathematical/algorithmic scope (explicitly deferred, not forgotten):**

- **CVRPTW** delivery windows, waiting, service start constraints, late-arrival prohibition.
- Departure-time-dependent congestion/travel times (TDVRP), hourly traffic forecasts.
- Explicit emissions/carbon optimization, fuel modeling, traffic-based emissions accounting; benefits must not be claimed from distance alone without assumptions/data.
- Heterogeneous truck capacities, different vehicle costs, multi-depot routing.
- Split deliveries, pickups, optional customers/prizes, multiple tours per truck, mandatory breaks, driver shifts, route duration bounds, precedence constraints.
- Vehicle loading in multiple dimensions, hazardous-material compatibility, live GPS/road incident updates, stochastic demand, live dispatch.

**`[APPROVAL — USER + TUTOR]`** Confirm that implementing a **static-distance CVRP** satisfies the Level B assessment even though the motivating ADEME scenario mentions travel duration and traffic. Make the distinction explicit in presentations; do not silently change cost definitions mid-project.

### 1.4 Meaning of “as optimal as possible”

- We seek the **best feasible routes within a declared and repeatable computational budget**, not an unsupported guarantee of global optimality on NP-hard instances.
- **Feasibility is mandatory**; an attractive distance with unserved customers or overloaded trucks is an invalid result.
- Use **multiple independent construction and improvement mechanisms**, optimize the expensive inner loops, tune on a training set, and benchmark against both a simple baseline and a strong external solver (subject to academic rules).
- Quantify the distance-to-reference gap and **any** quality–runtime trade-off; report worst cases and timeouts rather than hide them.
- Where an exact solver is used, call an answer *proven optimal* **only if the solver actually returned and documented a proof/status** (and matching model/metric).

---

## 2. What exists today: evidence and limitations

### 2.1 Existing artifacts (checked 2026-11-02)

| File | Purpose | Evidence found |
|---|---|---|
| `CesiCDP_CVRP_Detailed_Modeling.ipynb` | Detailed first-checkpoint notebook | 68 cells = 39 Markdown + 29 code; 19 embedded PNG figure outputs; all code cells have recorded execution counts; no recorded error outputs |
| `CesiCDP_CVRP_Mathematical_Modeling.ipynb` | Earlier/simpler modeling draft | Exists, **do not confuse it with** the detailed current draft |
| `CesiCDP_CVRP_Modeling_Package.zip` | Modeling notebook + example data | Includes A-n32-k5 `.vrp` and `.sol` and an earlier short README |
| This `README_CesiCDP_CVRP_Project.md` | Detailed project execution specification | Master plan, tracked approvals, parameters, future tests and release gates |

**Verification nuance:** saved execution counts/images and absence of saved exceptions were inspected. That is **not** equivalent to a fresh end-to-end execution on another machine. A clean-environment rerun remains on the TODO list.

### 2.2 Completed modeling functions/topics

- [x] Formal directed graph: depot `0`, customer set, available vehicle set, route arcs.
- [x] Symbolic data: `n`, `K`, `Q`, customer demands `q[i]`, cost matrix `d[i,j]`, optional coordinates.
- [x] Binary arc-selection `x[i,j,k]`, assignment `y[i,k]`, vehicle-use `z[k]`, auxiliary MTZ order `u[i,k]`.
- [x] Objective: minimize aggregate fixed travel **distance**, including departure and return legs.
- [x] Customer coverage, per-vehicle incoming/outgoing degree, depot degree, capacity, subtour elimination, domains.
- [x] MTZ argument handling even **zero-demand customers**.
- [x] Proof that CVRP is NP-hard by specialization to one capacious vehicle (TSP).
- [x] Python synthetic instance generation for uniform/clustered distributions and adjustable seed.
- [x] Input consistency checking, plots, toy valid/invalid route examples.
- [x] Independent route-list validator and an ILP equation certificate on provided routes.
- [x] Embedded A-n32-k5 benchmark example; saved outputs report reference cost 784 and feasibility checks.
- [x] Notes about rounding and scaling of a full three-index ILP.
- [x] Scientific reference list in the notebook.

### 2.3 Known review items / limitations of current notebook

- [ ] **`[APPROVAL — TUTOR]`** Validate the exact mathematical formulation and proof; record feedback and corrected equations.
- [ ] **`[APPROVAL — USER + TUTOR]`** Resolve **at most `K`** vs **exactly `K` nonempty routes**. Draft assumes *at most*.
- [ ] Verify all big-M/order bounds and degree/flow constraints under `n=1`, `K=1`, `K>n`, `q_i=0`, `q_i=Q`, equal coordinates, asymmetric and zero distances, unsplittable demands, infeasible fleet.
- [ ] Check whether zero-customer instances should be accepted as a trivial empty plan; current teaching model expects at least one customer. **`[APPROVAL — USER]`**
- [ ] **`[RESEARCH]`** Cross-check graph metrics, directed distances, non-metric costs, `EUC_2D`/`CEIL_2D`/`EXACT_2D`/`EXPLICIT` format handling per chosen benchmark family.
- [ ] Improve ID reconciliation between source file labels, internally reindexed depot/customer IDs, `.sol` route IDs, and exported routes; test a file with a **depot that is not the first node**.
- [ ] Test that the current loader does **not** mistakenly round already-integral explicit weights or reapply an unsuitable policy; preserve the original exact matrix when required.
- [ ] Verify metadata-derived fleet-size logic: regex `-k#` is **family-dependent**, not a universal VRPLIB rule. Unknown `K` must be resolved from an authorized source/config rather than guessed.
- [ ] Clarify that synthetic instances can be **infeasible** despite the generator working; reject or flag them, never fabricate feasible routes.
- [ ] Add explicit assertions/checks for impossible `K`, demands exceeding capacity, and inconsistent provided route/vehicle labels.
- [ ] Rerun notebook with **Restart Kernel → Run All** in a clean environment and retain a reproducibility log.
- [ ] Add a correction log recording equation, reason, tutor feedback, code validation and reviewer.
- [ ] Decide whether model variables need only conceptual mathematical presentation (current stage) or a small exact model implementation in the final project.

---

## 3. Decisions and approvals required

**No open academic or modeling choice should be silently treated as settled.** Use the table below as the decision register. “Provisional default” is a *proposal*, not approval.

| ID / Priority | Decision / research | Provisional default or options | Owner / gate | Why it matters |
|---|---|---|---|---|
| D01 **BLOCKER** | **Up to K vs exactly K trucks used?** | Up to `K` with optional unused trucks; verify wording | **[APPROVAL — USER + TUTOR]** | Changes depot-use constraints, feasibility and comparability |
| D02 **BLOCKER** | Distance vs duration as graded objective | Static **distance**, matching VRPLIB reference | **[APPROVAL — TUTOR]** | Avoid apples-to-oranges gap values |
| D03 **BLOCKER** | Will solving 20 VRPLIB datasets + synthetic satisfy instance coverage? | At least 20 **distinct** real CVRP benchmarks, synthetic as supplemental | **[APPROVAL — USER + TUTOR]** | Meets stated validation requirement conservatively |
| D04 **BLOCKER** | Acceptable benchmark families / size spread | A/B/P/E/M/X mixture with approved manifest | **[APPROVAL — TUTOR] [RESEARCH]** | Fair, representative and cost-compatible results |
| D05 **BLOCKER** | Fleet limits for files without `VEHICLES` | Use file/family official fleet info or approved override; fail otherwise | **[APPROVAL — USER + TUTOR] [RESEARCH]** | Hidden fleet changes invalidate comparisons |
| D06 **BLOCKER** | Benchmark edge-weight policies, including half ties | Explicit per-instance rounding policy and published route-cost checksum | **[RESEARCH] + reviewer sign-off** | Tiny rounding errors corrupt gap claims |
| D07 **BLOCKER** | Third-party solvers in submission? | Implement own ALNS; PyVRP/HGS as **clearly labeled comparison**, not disguised authorship | **[APPROVAL — TUTOR]** | Academic integrity, grading expectations |
| D08 High | Main metaheuristic choice | ALNS with local search; compare with HGS evidence | **[APPROVAL — USER + TUTOR] [RESEARCH]** | Strong solution quality and explainability |
| D09 High | Quality goals | Try for gaps significantly below 7%; report actual figures honestly | **[APPROVAL — USER]** | No guarantee possible; guides tuning |
| D10 High | Per-run compute budgets | Configurable seconds/iterations/no-improvement; compare at same wall-time | **[APPROVAL — USER]** | Quality/time fairness |
| D11 High | Available hardware and memory | Record OS, CPU, RAM, Python versions, concurrency | **[APPROVAL — USER]** | Performance/reproducibility/scalability |
| D12 High | Number of stochastic repetitions | Configurable `repeats`; suggested multiple independent seeds, justified by budget | **[APPROVAL — USER]** | Reliable mean/std/worst comparisons |
| D13 High | Is exact ILP benchmark required or optional? | Formulate fully; solve only small instances if useful and allowed | **[APPROVAL — TUTOR]** | Exact results versus main heuristic |
| D14 High | Parameter tuning policy | Separate tuning subset; freeze parameters before test | **[APPROVAL — USER]** | Avoid benchmark overfitting |
| D15 High | Dataset acquisition permissions/licenses | Retain sources, attribution, and permitted copies | **[RESEARCH]** | Submission packaging/provenance |
| D16 Medium | Road graph vs precomputed complete matrix | Model complete customer-level cost closure; road shortest paths are future preprocessing | **[APPROVAL — USER]** | Interface and memory design |
| D17 Medium | Symmetry support | Allow asymmetric matrices where valid; use asymmetry-safe cost updates | **[APPROVAL — USER]** | Generality vs code complexity |
| D18 Medium | What to do when no feasible initial solution is found | Run alternate construction/repair; return explicit failure, never invalid result | **[APPROVAL — USER]** | Reliability |
| D19 Medium | Parallel optimization / multi-start | Optional configurable parallel runs; record total CPU resources | **[APPROVAL — USER]** | Performance fairness |
| D20 Medium | Emissions/traffic treatment in final ADEME narrative | Discuss only as potential extensions; no unsupported carbon claim | **[APPROVAL — USER + TUTOR]** | Responsible interpretation |
| D21 Medium | Zero-customer and zero-demand handling | Zero-demand customers must be served; empty instance support optional | **[APPROVAL — USER]** | Boundary conditions |
| D22 Medium | Allowed algorithms/libraries and Python standard | Check PEP guidance, required originality and environment | **[APPROVAL — TUTOR]** | Compliance |
| D23 High | Concrete checkpoint dates and who submits what | Fill milestone dates from official course calendar | **[APPROVAL — USER + TUTOR]** | “Prosit 3,” final-before-defense, oral defense, July deadline |
| D24 Medium | Reference quality label | `optimal_proven`, `best_known`, or `unknown`; retain source and date | **[RESEARCH]** | Honest gap claims |
| D25 Medium | Termination and reproducibility | Deterministic seed for tests; repeated independent seeded runs for statistics | **[APPROVAL — USER]** | Reproducible experiments |
| D26 Medium | Packaging | One narrative final notebook + scripts/tests/data manifest; no bulky redundant outputs | **[APPROVAL — USER + TUTOR]** | Clear grading/replication |

**Recommended priority:** secure decisions **D01–D08** before implementing the main solver. All algorithm hyperparameters can remain configurable while defaults are tuned later.

---

## 4. Master configurable parameter register

### 4.1 Core rule: separate *schema* from *values*

**Never hard-code** customer count, number of trucks, shared capacity, demand values, depot/source identifiers, coordinates, pairwise costs, random seed, benchmark names, run budgets, neighborhood sizes, or plotting thresholds into solver logic. **Some mathematical definitions are fixed by CVRP** (serve every selected customer, no capacity violation, return to depot, no subtours); their **data** are variable.

All parameters below need: a documented type, units, valid range, source (dataset/config/derived), default policy, validation behavior, experiment logging, and a test that changes the parameter without changing solver source.

#### A. Required instance inputs (all variable by instance)

| Field / symbol | Type and validation | Source; implementation requirement |
|---|---|---|
| `instance_id` | Nonempty unique string | Filename/manifest; included in outputs |
| `n_customers` (`n`) | Integer >= 0 (or >=1 if agreed) | Derived from selected customer records |
| `customer_ids` (`C`) | Unique IDs; may be non-contiguous externally | Source dataset; internal contiguous mapping |
| `selected_customer_ids` | Explicit subset if routing a subset of road-network clients | Dataset/config; **every selected** client mandatory |
| `depot_id` | Exactly one valid node | Dataset; internally may map to 0 |
| `depot_coordinates` | Optional valid `(x,y)` and coordinate reference/unit | Dataset or user-configured |
| `customer_coordinates` | Optional array `n×2`, finite numeric | Dataset; if unavailable, no geographic plot |
| `max_vehicles` (`K`) | Positive integer (unless empty-case policy) | Dataset, official benchmark rule, or **explicit override** |
| `vehicle_capacity` (`Q`) | Finite positive number | Dataset; **shared by every vehicle** |
| `customer_demands` (`q_i`) | Finite nonnegative, length `n` | Dataset, with demand units |
| `depot_demand` (`q_0`) | Normally 0 in base CVRP | Input check; normalize only with documented rule |
| `distance_matrix` (`d_ij`) | Valid nonnegative NxN; finite for required arcs | Official explicit matrix, Euclidean transform, or authorized road closure |
| `allowed_arcs` (`A`) | Optional directed arc mask, no illegal self-loop | Dataset/road reachability; default complete directed graph |
| `coordinate_unit` | e.g. dataset units, km, meters | Metadata; never call benchmark units “kilometers” without evidence |
| `cost_unit` | Numeric unit/scale of objective | Metadata; comparability check required |
| `distance_policy` | Enum: `raw`, `nearest_integer`, `floor`, `ceil`, `exact_scaled`, `explicit` (per source family) | Manifest; **not universal nearest-integer** |
| `edge_weight_type` | e.g., `EUC_2D`, `CEIL_2D`, `EXACT_2D`, `EXPLICIT` | File; handle or explicitly reject unsupported types |
| `edge_weight_format` | e.g., `FULL_MATRIX`, `LOWER_ROW` where appropriate | File; preserve directed/asymmetric semantics |
| `source_node_id_mapping` | Reversible map source IDs <-> internal IDs | Loader and exporter; unit tests |
| `fleet_rule` | Enum: `at_most_k` / `exactly_k` | **Approved problem policy**; test both if supported |
| `demand_unit` | E.g., items, kg, abstract capacity units | Instance metadata; no assumptions |
| `cost_symmetric` | Derived boolean or asserted by source | Optimize moves correctly if false |
| `triangle_inequality` | Optional verified property; do not assume | Document heuristic applicability |
| `instance_source_url` | Valid reference/provenance | Manifest |
| `instance_checksum` | SHA256 or equivalent | Verify unchanged data |

**Explicit validation constraints:** `q_i <= Q` for every customer; total demand `<= KQ` necessary; if unmet, reject as infeasible. Neither condition alone is sufficient to guarantee feasible bin packing. No fabricated routes on infeasible inputs. Check matrix shape `(n+1,n+1)`, numeric finiteness, diagonal handling, coordinate alignment, and customer ID cardinality.

#### B. Configurable synthetic scenarios (for analysis, never mistaken for graded benchmarks)

| Field | Purpose |
|---|---|
| `synthetic.n_customers` | Size of generated instance |
| `synthetic.max_vehicles` | Available fleet size |
| `synthetic.vehicle_capacity` | Shared truck capacity |
| `synthetic.min_demand`, `max_demand` | Demand range |
| `synthetic.demand_distribution` | Uniform, skewed, bimodal, zero-inflated, concentrated, etc. (if implemented) |
| `synthetic.layout` | Uniform, clustered, mixed, grid, elongated, random (implemented options must be documented) |
| `synthetic.cluster_count`, `cluster_spread` | Geographic clustering characteristics |
| `synthetic.coordinate_bounds` | Generating coordinate domain, configurable units |
| `synthetic.depot_xy` | Depot placement |
| `synthetic.distance_policy` | Distance generation/rounding |
| `synthetic.seed` | Deterministic generator seed |
| `synthetic.ensure_feasible` | Optional feasibility-aware generator strategy; document method and limitations |
| `synthetic.selected_customers` | Optional customer subset selection, preserving mandatory service |
| `synthetic.asymmetric_cost_option` | Optional directed synthetic cost stress test |
| `synthetic.zero_demand_probability` | Validate zero-demand edge case |

**Currently implemented synthetic generator:** `n_customers`, `max_vehicles`, `vehicle_capacity`, `min_demand`, `max_demand`, `coordinate_max`, `depot_xy`, `layout` (`uniform`/`clustered`), `seed`, `distance_policy` (`raw`/`nearest_integer`/`ceil`). Everything else in this table is a **future optional parameter**, not an existing feature.

#### C. Construction algorithm configuration (future)

| Field | Options / role |
|---|---|
| `construction.method` | Savings / greedy cheapest insertion / parallel insertion / randomized multistart |
| `construction.savings_lambda` | Clarke–Wright savings weighting if weighted variant used |
| `construction.seed_customer_policy` | Furthest, cheapest, clustered, random |
| `construction.randomization_strength` | Randomized candidate selection to diversify starts |
| `construction.candidate_list_size` | RCL width / nearest-neighbor count |
| `construction.max_restarts` | Alternative attempts if no feasible construction |
| `construction.repair_budget` | Time/iteration cap for recovery |
| `construction.force_feasible` | Require independent validator before ALNS main loop |
| `construction.initial_route_limit` | Respect selected `K` policy; not hardcoded |

#### D. Local-search and ALNS configuration (future)

| Field | Meaning |
|---|---|
| `metaheuristic` | `alns` primary; optional `tabu`/`hgs` research paths only if approved |
| `max_iterations`, `time_limit_seconds`, `max_no_improvement` | Alternative or combined stopping rules |
| `random_seed`, `restart_seeds`, `number_of_starts` | Reproducibility and intensification |
| `destroy_min_fraction`, `destroy_max_fraction` | Limits on removed customers as fractions of variable `n` |
| `destroy_min_count`, `destroy_max_count` | Optional absolute count bounds after range clipping |
| `destroy_operators` | Enabled removal operators: random, worst, related, route, segment |
| `repair_operators` | Enabled insertion operators: cheapest, regret-2, regret-k, randomized |
| `relatedness_weights` | Relative influence of distance, demand, route membership |
| `regret_k` | Regret insertion depth |
| `operator_initial_weights` | Initial ALNS selection weights |
| `operator_learning_rate` (`reaction_factor`) | Weight adaptation strength |
| `operator_update_period` | Iterations between weight recalculations |
| `score_new_best`, `score_better`, `score_accepted`, `score_rejected` | Operator reward scheme |
| `acceptance.method` | Strict improvement, simulated-annealing, late acceptance, etc. |
| `acceptance.initial_temperature`, `cooling_rate`, `min_temperature` | Annealing control; well-defined calibration |
| `acceptance.worsening_target_probability` | Optional temperature calibration target |
| `local_search.moves` | 2-opt, relocate, swap, Or-opt, 2-opt*, cross-exchange, SWAP* (as implemented) |
| `local_search.first_vs_best_improvement` | Quality-vs-speed choice |
| `local_search.candidate_neighbors` | `k` nearby clients (configurable; never exceed `n-1`) |
| `local_search.max_passes`, `move_evaluation_budget` | Search effort limit |
| `infeasible_search.enabled` | Optional temporary penalized infeasible intermediates; **never** invalid final output |
| `capacity_penalty`, `penalty_adjustment` | Only if temporary infeasibility approved and implemented |
| `stagnation_restart_after`, `perturbation_strength` | Escape local optima |
| `elite_pool_size`, `elite_diversity_threshold` | Optional quality/diversity memory |
| `route_cost_cache`, `delta_evaluation`, `vectorization` | Performance toggles for ablation/testing |
| `parallel_workers` | Optional; track effective total CPU resources |
| `checkpoint_interval`, `log_interval` | Intermediate diagnostic frequency |
| `early_stop_target_cost` | Optional **known target** for stopping; not an oracle for move acceptance |

Every operator's conditions and search parameters must be documented with its allowed range, a tested default, and logs. No unsupported knob should be exposed as though functional.

#### E. Experimental configuration (future)

| Field | Requirement |
|---|---|
| `benchmark_manifest` | Explicit list of >=20 distinct named files; source URL and checksum |
| `train_instance_ids`, `test_instance_ids` | Separate tuning from evaluation |
| `run_seeds` / `repetitions` | Independent repeated trials |
| `per_instance_time_budget_seconds` | Same budget for methods being compared |
| `per_instance_iteration_budget` | Secondary diagnostic; not a fair cross-method time substitute |
| `hardware_profile` / `workers` | Record CPU, RAM, concurrency, OS |
| `warm_up_runs` | Optionally mitigate startup compilation/caching effects |
| `baseline_methods` | Construction-only, ALNS, optional PyVRP/HGS, optional exact small-instance solve |
| `cost_validation_tolerance` | Appropriate numeric tolerance by metric/scale |
| `reference_cost`, `reference_type`, `reference_source`, `reference_date` | Traceable optimum/BKS distinction |
| `plot_types`, `figure_dpi`, `figures_directory` | Reproducible visualizations |
| `results_directory`, `save_route_files`, `save_run_logs` | Persist raw runs and final routes |
| `confidence_level`, `bootstrap_reps` | Statistical reporting choices (if used) |
| `timeout_policy`, `failed_run_policy` | Failed/infeasible/time-limited runs reported, not discarded |

#### F. Environment/project configuration (future)

`python_version`, `dependency_versions`, `platform`, `cpu_model`, `available_ram_gb`, `blas_threads`, `process_count`, `time_zone_for_logs`, `project_root`, `data_dir`, `output_dir`, `log_level`, `test_data_dir`, `deterministic_mode`, `dataset_download_policy`, `license_tracking`, `seeds`, `run_tag`, `git_commit`, `manifest_version`.

**No need to hard-code an arbitrary default**: define a validated config schema and support command line / YAML / JSON overrides. Defaults may exist for *convenience* if disclosed, measured and not misleadingly treated as universal constants.

---

## 5. Mathematical model and formal validation checklist

### 5.1 Definitions (parameterized, basic CVRP)

- `C={1,...,n}`: customers; `V={0} ∪ C`: nodes; `F={1,...,K}`: vehicles.
- `A={(i,j)∈V×V:i≠j}` for the full directed customer closure, or a correctly represented allowed-arc subset.
- `q_i ≥ 0`: customer demands; `Q>0`: shared capacity; `d_ij ≥ 0`: static distance.
- `x_ijk ∈ {0,1}`: vehicle `k` uses arc `i→j`.
- `y_ik ∈ {0,1}`: customer `i` is assigned to vehicle `k`.
- `z_k ∈ {0,1}`: vehicle `k` is active.
- `u_ik ∈ R_+`: MTZ order variable, zero when `i` unassigned.

**Objective:**

`min Σ_(k∈F) Σ_((i,j)∈A) d_ij · x_ijk`

**Must-have constraints:**

1. `Σ_k y_ik = 1` for each customer `i` (exactly one service).
2. `Σ_(j≠i) x_ijk = y_ik` for each `i,k` (one departure if assigned).
3. `Σ_(j≠i) x_jik = y_ik` for each `i,k` (one arrival if assigned).
4. `Σ_(j∈C) x_0jk = z_k` for each `k` (one depot departure if used).
5. `Σ_(i∈C) x_i0k = z_k` for each `k` (one depot return if used).
6. `Σ_(i∈C) q_i y_ik ≤ Q z_k` for each `k` (capacity).
7. `y_ik ≤ u_ik ≤ n y_ik` for each `i,k` (orders only for assigned customers).
8. `u_jk ≥ u_ik + 1 − (n+1)(1−x_ijk)` for each `i≠j∈C`, each `k` (MTZ subtour elimination).
9. Binary domains for `x,y,z`, nonnegative continuous domain for `u`, no self loops.
10. Optional truck-label symmetry breaking: `z_k ≥ z_(k+1)` when vehicles are identical (changes labels, not physical solutions).

**Nuance:** for allowed-arc subsets, change sums and graph assumptions consistently; do not keep undefined `x_ijk` variables or forget reachability. If benchmarking standard complete-node-distance CVRP, the full `A` above is appropriate.

### 5.2 Why this formulation works

- [x] Every physically valid route can induce `x,y,z,u` satisfying the equations.
- [x] Every solution satisfying the equations represents depot-connected routes with every customer exactly once, bounded load, and at most `K` active trucks; disconnected customer cycles are impossible because MTZ order would strictly increase around a cycle.
- [ ] Test independently that order inequalities still exclude subtours with zero demand.
- [ ] Verify numerical coefficient `n+1` is valid and not unnecessarily large; review stronger capacity-based or single-commodity-flow alternatives as research, without expanding scope.
- [ ] Decide whether optional lexicographic secondary objectives (e.g., fewer vehicles) are allowed. **Do not add a vehicle penalty to a distance-only benchmark objective without approval**.
- [ ] Verify vehicle-use interpretation and actual benchmark fleet convention.
- [ ] Prove/verify the reduction from metric TSP: one truck with `Q >= Σ_i q_i`, then the CVRP objective coincides with a depot-returning TSP. State the underlying decision version is NP-complete if claiming NP-completeness; **CVRP optimization is NP-hard**, not normally called NP-complete.
- [ ] Explain difference among exact model, solver, feasible solution, best-known solution, lower bound, optimality certificate, and heuristic.

### 5.3 Mandatory tiny-case audit before tutor sign-off

- [ ] `n=1, K=1` route `0→1→0` correctly represented.
- [ ] `n=2` with one capacious truck; both customer orders allowed.
- [ ] `K=1`, aggregate demand within capacity (TSP special case).
- [ ] `K=1`, aggregate demand over capacity ⇒ infeasible.
- [ ] `K>n`, unused trucks allowed when fleet rule is `at_most_k`.
- [ ] `K=n` each truck may visit one customer.
- [ ] One demand exactly `Q`: no other positive-demand customer may share truck.
- [ ] A customer with `q_i=0` remains mandatory.
- [ ] Aggregate demand `≤KQ` but impossible unsplittable packing: detect no feasible final solution.
- [ ] Two customers at same coordinates / zero-cost arcs: still exactly one service.
- [ ] Asymmetric `d_ij`: reversal of an entire route has different cost.
- [ ] Explicit invalid customer-only cycle: rejected by subtour constraints.
- [ ] Customer duplicated, omitted, unknown, depot in wrong position, invalid ID: rejected.
- [ ] Empty truck route handled according to `z_k` rule.
- [ ] `K=0`, negative demand, nonfinite distances/capacity, mismatched matrix dimensions: robust explicit error.
- [ ] Input with a nonzero depot ID normalized and mapped back correctly.

---

## 6. Full work breakdown and ordered TODOs

**Completion means a tangible artifact, independent validation evidence, and review sign-off.** Individual implementation tasks are **not** checked merely because a similar function exists in the modeling notebook.

### Phase 0 — Lock the project contract / first-model review (CURRENT)

**Owner:** mathematical lead + tutor; **exit:** signed scope and corrected model.

- [x] Capture assignment deliverable requirements and chosen Level B scope.
- [x] Create detailed modeling notebook and explanations.
- [x] Provide synthetic and real data visual demonstrations.
- [ ] D01/D02: obtain fleet rule and static-distance objective approval. **[APPROVAL — TUTOR] [BLOCKER]**
- [ ] D07/D08: clarify own-algorithm versus external-comparison policy and choose primary metaheuristic. **[APPROVAL — TUTOR]**
- [ ] Confirm actual Prosit 3 meeting date, final notebook deadline, defense date, and relevance/year of “12 July”. **[APPROVAL — USER + TUTOR]**
- [ ] Recheck the full ILP on tiny cases with independent route/constraint logic.
- [ ] Recheck mathematical proof and MTZ coefficients with a reviewer.
- [ ] Run the modeling notebook cleanly from scratch on the agreed environment.
- [ ] Record all feedback in a **dated review/corrections table**, with equation references.
- [ ] Correct notebook and update formulation version; archive old draft.
- [ ] Capture tutor review evidence/approval; mark “Modeling accepted” only then.

**Exit evidence:** `model_review.md` (questions, answers, signature/date), updated modeling notebook, clean execution log and tests.

### Phase 1 — Project engineering and data pipeline (NEXT TECHNICAL PHASE)

**Owner:** data/implementation lead; **exit:** arbitrary approved datasets can be loaded and validated with no solver changes.

- [ ] Set up repository structure, environment file, `requirements.txt`/lockfile, `pytest`, formatter/linter, `.gitignore`, dataset provenance manifest.
- [ ] Create `CVRPInstance` canonical contract and `SolverConfig` separate from data values.
- [ ] Implement configuration loading from CLI and YAML/JSON; validate types/ranges and reject unknown options.
- [ ] Implement `vrplib.read_instance` as primary benchmark loader; keep fallback explicitly limited or remove from production path.
- [ ] Preserve original identifiers, depot position and full external↔internal mapping.
- [ ] Support approved `EUC_2D` and `EXPLICIT` cases initially; investigate additional weight types and rounding with source-specific tests.
- [ ] Define fleet-rule lookup/override policy and prohibit undocumented inference.
- [ ] Preserve `Q`, `K`, demand and distance **units** and source metadata in the in-memory instance and results.
- [ ] Create synthetic generator interface and verify seed reproducibility.
- [ ] Derive or load pairwise costs; avoid unnecessary full matrix for very large datasets when approved.
- [ ] Implement pre-solve feasibility checks, with direct failure messages.
- [ ] Implement reference solution reader and cost audit; check published reference route costs against source.
- [ ] Create an initial **benchmark manifest** with family, n, K, Q, distance rule, BKS/proven label, source and checksum.
- [ ] Add parser tests for missing demand, malformed file, bad fleet info, non-first depot, explicit matrix, rounded metrics, noncontiguous IDs.
- [ ] Test all supported configurable fields by loading two very different instances without changing source.

**Exit evidence:** `src/data.py`, `src/config.py`, manifest, tests, sample CLI and documented input/output schema.

### Phase 2 — Standalone feasibility and cost evaluator

**Owner:** mathematical lead + software lead; **exit:** route quality and validity are evaluated **independently of optimization**.

- [ ] Define canonical solution: list of routes in internal customer IDs (no depot inside lists), and optional mapping of route to truck.
- [ ] Define objective: sum of `d[0,r1] + Σ d[ri,r(i+1)] + d[rlast,0]` over used routes; empty route contributes zero.
- [ ] Check all selected customers visited exactly once, no unknown IDs, depot not duplicated, no empty/malformed route leakage.
- [ ] Check fleet rule (`<=K` or `==K`) and `Σ q_i <= Q` on each route.
- [ ] Check allowed arcs/reachability, matrix indices and numerical validity.
- [ ] Validate objective by both a simple independent reference implementation and the optimized incremental evaluator.
- [ ] Reconstruct `x,y,z,u` for small cases and verify ILP equations **as an independent cross-check**, not merely a second call to same logic.
- [ ] Return structured diagnostics (`feasible`, errors, per-route load/cost, total distance, used vehicles, unused capacity).
- [ ] Test symmetric and asymmetric costs, zero distances, duplicate customers, absent customers, oversized demand, empty fleet.
- [ ] Make final-output validation mandatory; optimizer cannot report an invalid incumbent as feasible.
- [ ] Add serialization and reload of solution routes including metadata and cost checksum.

**Exit evidence:** `src/validate.py`, independently written tests, round-trip sample `.sol` export/reload.

### Phase 3 — Construction heuristics and lower bounds

**Owner:** algorithm lead; **exit:** valid starting routes with measured baseline cost.

- [ ] **[RESEARCH]** Review Clarke–Wright savings, sequential/parallel cheapest insertion and randomized construction.
- [ ] Implement at least two construction strategies when feasible (e.g., sequential insertion and savings); document their different failure modes.
- [ ] Respect hard fleet bound, capacity and mandatory customers during every insertion.
- [ ] Implement candidate lists and cost-delta evaluation without repeated full-route recomputation.
- [ ] Add configurable tie breaking and seed; deterministic when asked.
- [ ] Handle construction failure by alternate seeds/operators/repairs; do not silently increase `K`.
- [ ] Stop after explicit recovery budget and report `no_feasible_solution_found` without claiming mathematical infeasibility unless proven.
- [ ] Compute easy lower bounds where valid: demand-based truck bound, useful assignment/one-tree/relaxation bounds if justified.
- [ ] Validate **every** initial solution with independent checker and log initial cost.
- [ ] Demonstrate small construction runs graphically, with route load bars and distance totals.
- [ ] Benchmark construction-only costs/times on diverse small and medium instances.

**Exit evidence:** `src/construct.py`, proof-of-feasibility tests, baseline table and figures.

### Phase 4 — Local-search neighborhoods and accelerated move evaluation

**Owner:** algorithm lead; **exit:** reliable, improving neighborhood operations with verified deltas.

- [ ] Intra-route 2-opt (for asymmetric distances, accurately evaluate reversal and changed internal arcs).
- [ ] Intra/inter-route relocate of one customer.
- [ ] Intra/inter-route swap.
- [ ] Or-opt (move short sequence, configurable length).
- [ ] 2-opt* between routes (edge exchange; preserve capacity and route connectivity).
- [ ] **[OPTIONAL] [RESEARCH]** Cross-exchange and `SWAP*` neighborhoods; performance justification.
- [ ] Implement each operator with a clear mathematical delta formula and constraints.
- [ ] Unit-test delta == full independently recomputed cost within tolerance for thousands of seeded trial moves.
- [ ] Reject capacity/fleet/coverage-breaking moves (or carefully account for approved penalized infeasible search).
- [ ] Implement first-/best-improvement policy and configurable neighborhood scanning.
- [ ] Candidate neighbor lists, cache invalidation, incremental route load updates, and pruning.
- [ ] Confirm a local minimum for enabled neighborhoods when requested (no improving legal move remains within stopping budget).
- [ ] Compare operators individually and in combination on a disjoint development set.
- [ ] Add unit tests for route deletion/creation, singleton routes, zero demand, asymmetric costs, shared depot.

**Exit evidence:** `src/moves.py`, randomized delta tests, per-neighborhood ablation table.

### Phase 5 — Candidate ALNS metaheuristic (conditional on algorithm-selection gate A0)

**Owner:** algorithm lead; **entry gate:** §17 A0 comparative prototype must approve ALNS or choose a stronger own-implementation path; **exit:** configurable, high-quality and reproducible best-feasible route search.

- [ ] Specify algorithm formally: state, current/accepted/best solutions, neighborhood, destroy/repair operators, acceptance, weights and stopping.
- [ ] Implement **random removal** and **worst-cost removal**.
- [ ] Implement **related/Shaw removal** using configurable customer distance/demand/route features.
- [ ] Implement **route/cluster/segment removal** if it improves meaningful test cases.
- [ ] Implement **greedy insertion** and **regret-k insertion**, each respecting capacity and `K`.
- [ ] Implement randomized tie-breaking/diversification with recorded seeded RNG.
- [ ] Implement adaptive roulette/weighted operator selection with verified nonnegative normalized probabilities.
- [ ] Implement operator rewards (new best, improvement, accepted, rejected) and periodic weight adaptation.
- [ ] Implement acceptance policy: optionally simulated annealing with calibrated temperature and cooling schedule; document worse-move policy.
- [ ] Embed efficient local search after repair or on selected incumbents.
- [ ] Update best feasible solution **only after independent checks** (or sound incremental invariant checks plus periodic full validation).
- [ ] Add perturbation/restarts after no-improvement threshold.
- [ ] [OPTIONAL] Elite-solution pool or path-relinking for further intensification.
- [ ] Enforce time, iteration, no-improvement, memory, and cancellation limits; save best solution on graceful stop.
- [ ] Record iteration-level diagnostics: current/best cost, accepted vs rejected, operator use, runtime, feasibility, stagnation, improvements.
- [ ] Test determinism for fixed seed, and controlled diversity across different seeds.
- [ ] Run serious scalability/quality tests, not just notebook demonstrations.

**Exit evidence:** `src/alns.py`, flowchart/pseudocode, route and convergence visualizations, quality/runtime table.

### Phase 6 — Performance engineering for thousands of customers

**Owner:** algorithm + performance lead; **exit:** empirically demonstrated scaling with known memory footprint.

- [ ] Profile CPU hotspots using a reproducible profiler, and prioritize measured bottlenecks.
- [ ] Estimate memory: full `float64` `N×N` distance matrix uses approximately `8N²` bytes, without extra arrays; e.g. `N=5001` about **200 MB decimal** for one matrix alone.
- [ ] Avoid building full three-index ILP arrays for thousands of customers (`O(Kn²)` decision variables) unless intentionally solving small cases.
- [ ] Use incremental cost deltas, neighborhood restriction, efficient route arrays, caching and selective recomputation.
- [ ] Consider vectorization, Numba, compiled critical loops, or efficient C/C++ backed packages **only when allowed and properly documented**.
- [ ] Avoid unnecessary matrix copies, quadratic temporary arrays, dense intermediate history, repeated route reconstruction and heavy plots inside optimization loop.
- [ ] Establish performance milestones at increasing sizes; report actual max tested.
- [ ] Profile peak RSS memory, runtime, iterations/sec, best-gap improvement per second, worst-case time.
- [ ] Use seeded multi-start with independent workers only if resource-normalized comparisons are possible.
- [ ] **[RESEARCH]** For >1,000–5,000 clients, evaluate hierarchical cluster/route-first-decompose approaches if plain ALNS stalls; verify effect on global quality.
- [ ] Distinguish algorithmic time complexity estimates from measured scaling plots.
- [ ] Report whether time budget yields useful improvements and whether high-quality goals remain achievable at large scale.

**Exit evidence:** profiler report, scaling charts, memory data, optimization decisions with before/after tests.

### Phase 7 — Exact comparisons and external strong reference solvers

**Owner:** modeling + algorithm leads; **exit:** credible quality comparisons, with no falsely labeled optimum.

- [ ] **[APPROVAL — TUTOR]** Confirm whether an exact MILP solver is expected for some instances.
- [ ] If allowed, implement small CVRP ILP in PuLP/CBC, Gurobi, or other approved solver; reuse the validated model.
- [ ] Log solver statuses: optimal proven, feasible with bound, time limit, infeasible proven, error; do not conflate them.
- [ ] Validate MILP-extracted routes using the same independent checker.
- [ ] For tiny instances, cross-check against exhaustive enumeration/DP where tractable.
- [ ] **[APPROVAL — TUTOR]** If external comparison allowed, run a strong open-source baseline such as **PyVRP (current versions use iterated local search, ILS)** or Vidal's separate **HGS-CVRP** with a documented version and matched metric/fleet/time/resources.
- [ ] Clearly label third-party results as baselines; **do not present them as a self-developed algorithm**.
- [ ] Compare construction-only, own ALNS, optional exact/baseline results with paired instances and comparable budgets.
- [ ] If own method misses quality target, investigate root causes and adapt operators/tuning/strategy before finalizing.

**Exit evidence:** small-instance proof/bound table and/or independently reported external baseline table.

### Phase 8 — Experimental protocol and 20+ reference instances

**Owner:** experiments lead; **exit:** frozen, reproducible evaluation plan approved before final tests.

- [ ] **[APPROVAL — TUTOR]** Fix official benchmark families and interpretation of reference fleet/rounding.
- [ ] Build a manifest with **at least 20 distinct `.vrp` instances**, not merely 20 repetitions.
- [ ] Stratify by n (small/medium/large/very large), spatial pattern, demand/capacity pressure, fleet size and benchmark family.
- [ ] Include clustered, dispersed and mixed types where the family supports them; synthetic experiments separately supplement rather than substitute.
- [ ] For each reference, store dataset name, node count, K, Q, total demand, coordinate/matrix type, rounding rule, reference value, reference **status**, source date and checksum.
- [ ] Audit at least one **published reference route** per family against parsed costs whenever accessible; flag discrepancies immediately.
- [ ] Separate tuning and final evaluation instances; freeze config once evaluation begins.
- [ ] Choose number of repetitions and seeds; predeclare a seed list, including failures.
- [ ] Choose budgets (wall-clock primary, iterations secondary) and same hardware process policy.
- [ ] Define metrics, baseline methods, timeout/infeasible reporting, success thresholds and plots **before** examining final results.
- [ ] **[APPROVAL — USER]** Approve the computational budget and hardware restrictions.
- [ ] Create benchmark runner output that stores every raw trial, not only favorable best runs.

**Exit evidence:** `experiments/manifest.csv`, `experiments/protocol.md`, frozen configuration, seed list.

### Phase 9 — Run experiments and interpret statistics

**Owner:** experiments + algorithm leads; **exit:** validated raw results, statistical figures, honest conclusions.

- [ ] Execute all distinct >=20 reference instances, ensuring independent feasibility validation of every result.
- [ ] For randomized methods, repeat each selected instance according to approved repetition plan; preserve every seed and failure.
- [ ] Record best/final/initial distances, best-known reference, gap, runtime, iterations, max memory, routes, loads, statuses, algorithm version and settings.
- [ ] Compute gap only using equivalent metric and fleet rules; flag when reference cost/type absent.
- [ ] Report **best, mean, median, standard deviation, maximum/worst, quantiles** of gaps (as meaningful) and runtime.
- [ ] Report feasibility rate **over all attempted runs**, including timeouts/failures; do not compute quality mean without disclosing feasibility coverage.
- [ ] Plot gap versus n, runtime versus n, quality versus time, distribution by family, load utilization, parameter sensitivity, convergence, success rate, memory versus n.
- [ ] Use error bars/boxplots/violin plots for repeated runs; provide uncertainty intervals where sample sizes warrant.
- [ ] Compare paired seeds/instances fairly; use proper statistical tests/bootstrapping only when assumptions and multiple-comparison issue are discussed.
- [ ] Perform **ablation studies** (no local search, no adaptive weights, operator subset, one seed vs multi-start) to show what improves quality.
- [ ] Run sensitivity experiments for `K`, `Q`, demand distribution, seed, destroy fraction, candidate count and time budget, but **do not change reference benchmark constraints when calculating official reference gaps**.
- [ ] Analyze outliers, hard cases and whether complexity/precision/candidate lists explain results.
- [ ] Document nonconvergence, infeasible outputs, cutoff cases, and memory limits explicitly.
- [ ] Write justified improvements and distinguish evidence from speculation.

**Exit evidence:** raw CSV/Parquet, route files, plots, benchmark narrative, table of gaps and failure statuses.

### Phase 10 — Storytelling final Jupyter Notebook and delivery package

**Owner:** notebook/documentation lead; **exit:** complete reproducible deliverable.

- [ ] Structure narrative: ADEME context → formal CVRP problem → why NP-hard → validated ILP → why scalable heuristic → algorithm → demonstration → 20+ experiment results → limitations → next steps.
- [ ] Integrate **corrected, tutor-approved** modeling equations/proof from Phase 0.
- [ ] Document exact-model use (only formulation, small solved cases, bounds, or comparisons as actually performed).
- [ ] Give ALNS step-by-step equations and pseudocode, state variables, neighborhoods, operator adaptation, acceptance, stop rules.
- [ ] Provide readable PEP-oriented Python comments/docstrings and clear separation of data/model/optimizer/validator.
- [ ] Explain parameters in a compact table, their tuning ranges/defaults and their data provenance.
- [ ] Demonstrate multiple instances; run small examples quickly, link to stored full runs instead of rerunning heavy benchmarks in the presentation.
- [ ] Include statistics and interpretation, quality gaps, reference types, robustness, sensitivity, reproducibility, limitations, improvements.
- [ ] Include formal bibliography, software versions and dataset licenses/provenance.
- [ ] Ensure notebook restarts and runs from scratch in a fresh environment, or cleanly loads documented cached heavy results.
- [ ] Have team members review every cost claim, figure caption, legend, formula and sample output.
- [ ] Package notebooks, code, configs, data manifests, instructions and necessary small dataset copies; no broken absolute paths.

**Exit evidence:** final `.ipynb` or script, data manifest, README, environment lock, figures, references, executable quick-demo.

### Phase 11 — English oral presentation and final acceptance

**Owner:** all four team members; **exit:** credible demo and complete oral defense.

- [ ] Build professional English slides with context, mathematical model, algorithm flow, complexity and results first.
- [ ] Show representative route maps and convergence/quality plots, with readable labels and properly identified sources.
- [ ] Explain **what was completed**, **what is still pending**, risks and milestone dates; be transparent about blockers.
- [ ] Demonstrate a real run on a small instance; show input, config, feasible routes, distance, capacity checks and elapsed time.
- [ ] Precompute/retain known valid demo data for emergency fallback; never misrepresent cached results as a live run.
- [ ] Prepare live questions on MTZ, NP-hardness, objective, capacity, benchmark rounding, local-search move costs, stochastic reproducibility, BKS gap and timing.
- [ ] Assign one speaking segment to each of four members; rehearse seamless transitions and actual laptop/projector execution.
- [ ] Verify final notebook submitted by **the day before the defense** and oral presentation on **the final day of the block** (exact dates still to confirm).
- [ ] Reconcile the separate “12 July” project-submission wording with the current academic calendar. **[APPROVAL — USER + TUTOR]**

**Exit evidence:** slide deck, demo script, backup outputs, rehearsal checklist, submission receipt.

---

## 7. Algorithm strategy: maximize solution quality

### 7.1 Candidate ALNS architecture (subject to D07/D08 and §17 A0 approval)

```text
Approved CVRP data and distance policy
            │
            ▼
Independent input validation and feasibility prechecks
            │
            ▼
One or more construction heuristics (feasible initial plan)
            │
            ▼
Local search (2-opt / relocate / swap / 2-opt* / optional SWAP*)
            │
            ▼
ALNS search loop ────────────────────────────────────────────────┐
  1. choose destroy/repair operators adaptively                 │
  2. destroy a configurable number of client assignments       │
  3. repair respecting routes, capacity, fleet                  │
  4. run selective local improvement                            │
  5. validate / compute exact distance and feasibility         │
  6. accept/reject using configured acceptance policy          │
  7. update operator rewards, elite/best, convergence logs     │
  8. restart/perturb if stagnating                              │
  9. stop by time/iteration/no-improvement/memory budget ──────┘
            │
            ▼
Independent full solution validation + benchmark cost audit
            │
            ▼
Best **feasible** route set + cost + metrics + evidence
```

### 7.2 Quality-improvement ladder (implement in order; measure every gain)

1. **Correctness first.** Initial and final solutions always satisfy mandatory customers, depot, capacity and fleet policy.
2. **Strong initialization.** Compare multiple construction methods, randomized restarts, then choose favorable starting pool.
3. **Fast local neighborhoods.** Add relocation, swap, intra-route 2-opt and inter-route 2-opt*; use precise delta evaluation.
4. **Large-neighborhood diversification.** Multiple removal strategies and regret insertion, not just random disruptions.
5. **Adaptive operator choice.** Reward operators for actual improvements; guard against weight collapse/unbounded scores.
6. **Accept occasional worsening.** Configurable acceptance schedule to escape local minima while preserving best solution.
7. **Intensify high-quality incumbents.** Short aggressive local search, optional elite pool / path relinking.
8. **Tune empirically.** Budget, destroy fraction, neighbor lists, restart thresholds, operator weights and annealing based on disjoint tuning data.
9. **Profile.** Do not trade a large runtime regression for a negligible gap improvement without explaining quality/time tradeoff.
10. **Compare to strong alternatives.** Published reference optima/BKS and independently labeled HGS/PyVRP baselines if permitted.
11. **Escalation if target quality is not reached.** Evaluate stronger neighborhoods or HGS-based own implementation (if academic requirements permit), hybridization, intelligent decomposition, multistart/parallelization; justify added complexity.

### 7.3 No unverifiable “optimal” promises

The CVRP is NP-hard. A heuristic can be excellent but cannot generally certify optimality. Use the following precise labels:

- **Feasible:** all constraints checked, regardless of quality.
- **Best found by our algorithm:** minimum valid distance across its documented runs.
- **Best-known solution (BKS):** lowest known published reference at the stated source date, not automatically proven optimal.
- **Proven optimal:** backed by an exact certificate/official proof.
- **Lower bound:** rigorous number not exceeding true optimum, if its assumptions apply.
- **Gap to reference (%):** `100 × (C_ours − C_reference) / C_reference`.
- **Optimality gap:** only use this term when `C_reference` is actually proven optimal (or when reporting a mathematically defined solver bound gap).

**If gap to BKS is negative:** do not silently clip to zero; verify metrics, route feasibility, K and rounding; if still valid, potentially improved published best-known cost requires independent verification and careful reporting.

### 7.4 Experimental comparisons to avoid misleading claims

- Same `n, K, Q, q, d` and benchmark rounding for all methods.
- Compare under **equal wall-clock budget and stated hardware resources**; record runtime of construction and preprocessing.
- If an external solver uses extra CPU threads, record and normalize/describe total resources.
- Never use the published reference solution as a starting point in the **main** algorithm quality benchmark unless this is explicitly an oracle-seeded experiment, labeled separately.
- Never use the test instances to tune dozens of configurations and then report only the best without disclosing the search.
- Never merge distance-metric experiments with a time-dependent traffic objective in the same reference gap table.

---

## 8. Benchmark design and statistical analysis

### 8.1 Minimum dataset matrix (proposal; exact names require approval)

| Dimension | Planned coverage | Evidence to retain |
|---|---|---|
| Small `n` | Tiny and 30–100-client CVRPLIB cases | Correctness and small exact comparisons |
| Medium `n` | ~100–500 customers | Quality, runtime, parameter tuning |
| Large `n` | ~500–1,000 customers | Harder neighborhood/fleet tests |
| Very large `n` | >1,000, preferably several thousand if available | Realistic scalability/memory claims |
| Geometry | Uniform, clustered, mixed | Layout metadata, coordinate visualization |
| Capacity pressure | Loose, medium, tight (defined by demand-to-capacity ratios) | `Σq/(KQ)` and demand distribution |
| Fleet | Small/large `K`, optional unused trucks if allowed | Actual number used and prescribed fleet |
| Metric | Standard static distance, different approved weight conventions | Exact rounding and source IDs |

**`[RESEARCH]`** Standard public families do not all offer several-thousand-customer cases, and their formats/rounding may differ; therefore very-large cases may require separately labeled synthetic/scaling scenarios. Do **not** present synthetic cases as published BKS comparisons unless an independently valid BKS exists.

### 8.2 Raw results schema (one row *per algorithm / instance / seed / run*)

```text
run_id, timestamp_utc, git_commit, environment_id, algorithm_name, algorithm_version,
config_hash, instance_id, source_file_hash, benchmark_family, n_customers,
max_vehicles, vehicle_capacity, total_demand, demand_pressure, used_vehicles,
distance_policy, cost_unit, reference_cost, reference_type, reference_source,
seed, time_budget_seconds, iterations, status, feasible, invalid_reason,
initial_cost, final_cost, best_cost, gap_percent, total_wall_seconds,
preprocess_wall_seconds, solve_wall_seconds, peak_rss_mb, route_file,
operator_stats_file, convergence_trace_file, reviewer
```

`status` examples: `feasible_success`, `feasible_timeout`, `no_feasible_solution_found`, `invalid_output`, `input_infeasible_proven`, `input_error`, `resource_error`. Do not treat an algorithmic failure as proof the instance is infeasible.

### 8.3 Metrics to compute and interpret

1. Best and mean final **feasible** distance per instance and budget.
2. Gap to *proven optimum* or *BKS*, labeled distinctly.
3. Feasibility success rate and failure/timeout count.
4. Best/mean/median/worst gap and standard deviation across seeds per instance.
5. Execution time distribution, preprocessing and solution time separately, time-to-target where appropriate.
6. Improvement from construction-only baseline, absolute and relative.
7. Improvement versus local-search-only and ablated ALNS variants.
8. Capacity utilization distributions, actual vehicles used, empties/unused trucks.
9. Runtime scaling versus customers, total distance-matrix size, peak memory.
10. Sensitivity to time budget, removal fraction, candidate size, number of starts and random seed.
11. Per-family and per-size macro averages (**avoid hiding large outliers behind one grand mean**).
12. Quality-versus-time Pareto plots, convergence and stagnation curves.

**Statistics caution:** do not compare a quality average computed only on easy feasible runs against a method evaluated on all hard runs without stating the different denominators. Distinguish standard deviation **within instance across seeds** from variation **across heterogeneous instances**.

### 8.4 Gap audit

For every evaluated run:

1. Independently recompute `C_ours` from complete validated routes.
2. Confirm reference `C_reference>0`, correct metric, same instance, correct fleet and rounding.
3. Mark source/status: BKS or proven optimum.
4. Calculate `100*(C_ours/C_reference − 1)`; keep floating precision during computation.
5. Investigate unexpectedly negative gaps or discrepancies (do **not** modify reference data to make figures look better).
6. If reference is unavailable, report total distance, feasibility, and bounds where available; `gap_percent = null`.

### 8.5 Recommended figures (not decorations; each answers a question)

- [ ] Instance overview maps and route maps with depot/vehicle legends.
- [ ] Demand histogram + route load bars for representative small, medium, large cases.
- [ ] Distance heatmap only when readable; sample or downsample large matrices.
- [ ] Convergence curves: best/current cost versus iteration and elapsed time.
- [ ] Gap (%) versus number of customers; label BKS/optimum and show problem families.
- [ ] Runtime and memory versus instance size; log scales when appropriate.
- [ ] Boxplots/violin charts for repeated seeds on representative instances.
- [ ] Ablation comparison: construction vs local search vs ALNS variants.
- [ ] Parameter sensitivity heatmaps with *controlled* budgets.
- [ ] Feasibility/timeout frequency, including unsuccessful runs.
- [ ] Operator reward/selection frequency over time.
- [ ] Load utilization / unused fleet analysis.
- [ ] Quality-versus-time plot against baseline solvers, if approved.
- [ ] Pareto tradeoff: distance versus compute budget; explain budget differences.
- [ ] Dataset composition bar chart to demonstrate >=20 **different** instances.

---

## 9. Testing, correctness, and acceptance criteria

### 9.1 Test layers

**Unit tests**

- [ ] Parameter schema rejects invalid values and unknown options.
- [ ] Euclidean / explicit cost policy matches independently calculated benchmark examples.
- [ ] Source IDs round-trip through reindex/export.
- [ ] Every route move's delta matches full re-evaluation.
- [ ] Every allowed operator preserves or explicitly accounts for hard constraints.
- [ ] Seeded RNG gives deterministic behavior under documented serial settings.
- [ ] Selection weights are valid; no NaN, negative probability or overflow.
- [ ] Empty/singleton routes and unused trucks work.

**Property-based/randomized tests**

- [ ] For seeded valid instances, every reported solution covers customers exactly once.
- [ ] Route load never exceeds Q in final output.
- [ ] Move → inverse move restores same solution cost and assignments (where inverse is well-defined).
- [ ] Incremental load/cost caches remain equal to independent full recomputation.
- [ ] Customer index remapping preserves route cost under consistent matrix permutation.
- [ ] Shuffling labels of identical vehicles does not change physical objective.
- [ ] Increasing an unused capacity limit cannot invalidate an already feasible plan.
- [ ] Adding a new unused truck to an `at_most_k` instance cannot invalidate a previously feasible plan.

**Integration tests**

- [ ] `vrplib` loader → instance checks → solver → route checker → solution export → reload → same cost.
- [ ] A-n32-k5 published routes reproduce **784** under its published rounding convention.
- [ ] Several other reference families have audited matching route/cost conventions.
- [ ] Negative test for incorrect rounding produces a documented mismatch, not an accepted gap.
- [ ] All CLI/config overrides correctly change algorithm behavior with no code edits.
- [ ] Cancel/time-limit returns best **feasible** solution or a transparent failure.
- [ ] Fresh environment installs and runs a tiny example without manual notebook state.

**Performance tests**

- [ ] No unjustified quadratic move enumeration at scale; profile actual hotspots.
- [ ] Memory bounds recorded; no silent OOM at advertised sizes.
- [ ] Large-instance timeouts are handled deterministically/explicitly.
- [ ] Compare latest commit with prior benchmark on fixed seeds/hardware; investigate regressions.
- [ ] Full objective recomputation and independent feasibility audit periodicity documented.

### 9.2 Mandatory release gates

| Gate | Passing conditions | Review |
|---|---|---|
| G0 Modeling checkpoint | Equations/proof correct; tutor comments resolved | Tutor approval |
| G1 Data reliability | Approved datasets load with valid IDs, costs, K and Q | Independent reviewer |
| G2 Construction | Feasible initial solutions on documented test set | Independent validator |
| G3 Moves | All tested deltas accurate, no invalid moves emitted as valid | Test suite |
| G4 ALNS | Reproducible, feasibility-safe, quality improves over starting baseline on representative instances | Algorithm + statistics leads |
| G5 Benchmarks | ≥20 **distinct** instances; raw runs, consistent gaps and failure reporting | Experiment reviewer |
| G6 Quality | Grading threshold assessed honestly; attempts to improve outliers documented | Team + tutor if needed |
| G7 Reproducibility | New environment runs quick demo; full results traceable to config/seeds/versions | Peer reviewer |
| G8 Final defense | Final submission complete; English presentation/rehearsal ready | Whole team |

### 9.3 Project definition of “done”

A phase is **not done** until: (1) code/math artifact exists; (2) independent tests pass; (3) parameter values are externalized; (4) experiment or example evidence exists; (5) README + notebook are updated; (6) relevant teacher/user approvals are recorded; (7) no unacknowledged scope change occurs.

---

## 10. Anticipated tutor/professor questions

Each row is a **preparation task**, not a claim that the final answer has already been fully demonstrated.

| Question professor may ask | Expected defense / required artifact | Status |
|---|---|---|
| What is CVRP and how does it differ from TSP? | CVRP with capacities and `K` routes; TSP special case when `K=1`, Q sufficient | Modeling draft |
| Why did you choose distance rather than duration? | VRPLIB comparability; static distance scope explicitly agreed | Tutor approval pending |
| Why is the problem NP-hard? | Polynomial reduction from TSP with one sufficient-capacity truck | Modeling draft |
| Is it NP-hard or NP-complete? | Optimization NP-hard; properly specified decision version NP-complete | Review precision |
| What exactly are `x`, `y`, `z`, `u`? | Explain binary arcs, assignments, vehicle use and MTZ order | Modeling draft |
| Why is every customer visited exactly once? | Coverage + paired in/out-degree constraints | Modeling draft |
| Why does each active route start and end at depot? | Depot degree constraints and MTZ connectivity | Modeling draft |
| Why do flow constraints not eliminate subtours? | Disconnected customer-only cycle example | Modeling plot exists |
| How does MTZ prevent subtours? | Strict order increase around any customer cycle yields contradiction | Modeling draft |
| Why use `n+1` as big-M? | Bounds of `u` and redundancy when `x=0` | Review proof |
| What if `q_i=0`? | Still a mandatory visit; order-based MTZ prevents zero-load cycles | Demo exists |
| Why not use a load-based MTZ formulation? | Alternative may need care with zero demands; compare strength/size | Research |
| Exactly `K` or at most `K` vehicles? | Approved interpretation, updated constraints | **Decision D01** |
| Does total demand `<=KQ` guarantee feasibility? | No; unsplittable bin-packing counterexample | Modeling demo |
| What if every demand fits but no packing exists? | Solver may report no plan; distinguish failure from proof | Test pending |
| Are trucks identical? | Same Q, homogeneous assumptions; `z` labels interchangeable | Model |
| What if the depot is not ID 0? | Normalize internally; reversible source mapping | More tests |
| Why use a complete directed graph? | Pairwise customer closure; road network shortest paths may supply `d_ij` | Modeling draft |
| What if distances are asymmetric or nonmetric? | Directed model supports; some heuristic deltas need adaptation | Tests pending |
| What is a feasible solution vs optimal? | Constraint satisfaction versus minimum possible objective | Clear labels |
| Does your ILP scale to 3,000 clients? | Not naively; `O(Kn²)` arc variables, so use metaheuristic | Modeling chart exists |
| Why not solve everything with a MILP solver? | Exponential worst-case; exact small cases useful for bounds/tests | Evidence later |
| How did you choose ALNS vs tabu/SA/HGS? | Literature, quality/runtime tests, scalability and explainability | **Research + approval** |
| Is ALNS your own implementation? | Code, pseudocode, authorship and third-party disclosure | Pending |
| How do destroy/repair operators work? | Show small worked steps and cost/feasibility effects | Pending |
| Why are operator weights adaptive? | Rewards improve sampling of historically useful operators | Pending |
| Why accept worse solutions? | Escape local optima; best feasible always retained | Pending |
| Why local search after ALNS repair? | Intensification; operator ablation evidence | Pending |
| How is cost delta computed efficiently? | Explicit formulas and randomized recomputation tests | Pending |
| How do you know your solution is feasible? | Independent checker, no duplicate/unserved clients, loads/fleet | Partial modeling only |
| How do you handle failed construction/timeout? | Alternative attempts, explicit failure, best-so-far feasible plan | Pending |
| Why is the benchmark cost 784? | Published A-n32-k5 reference routes under approved rounding | Modeling example |
| Did your algorithm find 784? | **No**: reference was loaded/validated in modeling | Must say clearly |
| What is VRPLIB and how is it loaded? | `vrplib`, file parsing, cost/ID mapping, manifest | Partial modeling only |
| Why not use `np.round` indiscriminately? | Benchmark conventions differ; verify `EUC_2D` family policy | Documented |
| Why is a BKS not necessarily optimal? | Known incumbent versus certified global minimum | Must label |
| What does a negative BKS gap mean? | Recheck, may indicate valid improved BKS, not automatically error | Pending |
| What happens if no BKS exists? | Report distance and valid rigorous bounds, gap not fabricated | Pending |
| How many datasets were tested? | >=20 **distinct** required; must present manifest | Not started |
| Were random seeds controlled? | Reproducibility seeds and run logs | Not started |
| How did you tune parameters? | Separate training set, controlled budget, sensitivity/ablation | Not started |
| How robust is the solver? | Best/mean/std/worst, failures and repeated seeds | Not started |
| How fast is it on several thousand clients? | Measured runtime/memory, never inferred from a single sample | Not started |
| What are the algorithm's time/memory complexities? | Analyze worst-case dominant neighborhoods, measured profiles | Not started |
| How did you compare with external solvers fairly? | Matched metric, hardware, budget, version, author disclosure | Optional approval |
| Does minimizing distance guarantee CO₂ reduction? | Not necessarily; vehicle/traffic/load/fuel effects require evidence | Scope note |
| Why are plots necessary, what do they show? | Each graph answers hypothesis/constraint/quality question | Planned |
| How are limitations and future improvements justified? | Based on observed failures and controlled experiments | Planned |
| What did each of four members contribute? | Roles, signed reviews, Git history and presentation segments | Planned |
| Can a fresh environment reproduce the demo? | Clean install, run command, config + results hash | Planned |
| What changed after the first tutor review? | Dated equation/correction log | Pending |

---

## 11. Reproducibility, interfaces, and project structure

### 11.1 Proposed file layout (do **not** interpret uncreated files as existing)

```text
CesiCDP-CVRP/
├── README.md                        # this living plan (copy/rename as desired)
├── pyproject.toml                   # future dependency/tool config
├── requirements.txt                # pinned/recorded versions
├── .gitignore
├── notebooks/
│   ├── 01_cvrp_modeling.ipynb      # existing modeling notebook, copy here
│   ├── 02_cvrp_heuristics.ipynb    # TODO
│   ├── 03_cvrp_experiments.ipynb   # TODO
│   └── 04_cvrp_final.ipynb         # TODO
├── src/
│   ├── config.py                    # TODO: validation and override schema
│   ├── data.py                      # TODO: VRPLIB / synthetic loaders
│   ├── validate.py                  # TODO: independent checker
│   ├── construct.py                 # TODO: feasible starts
│   ├── moves.py                     # TODO: local search
│   ├── alns.py                      # TODO: own metaheuristic
│   ├── exact_small.py               # OPTIONAL: MILP tests
│   └── visualization.py            # TODO: plot utilities
├── configs/
│   ├── example.yaml                 # TODO
│   ├── alns_tuned.yaml              # TODO
│   └── benchmark_protocol.yaml      # TODO
├── data/
│   ├── benchmark_manifest.csv       # TODO
│   ├── reference/                  # source files / checksums
│   └── synthetic/                  # seeded scenarios
├── experiments/
│   ├── protocol.md                  # TODO
│   ├── raw_results.csv              # TODO
│   ├── routes/                      # TODO
│   ├── convergence/                 # TODO
│   └── figures/                     # TODO
├── tests/
│   ├── test_data.py                 # TODO
│   ├── test_validator.py            # TODO
│   ├── test_moves.py                # TODO
│   ├── test_alns.py                 # TODO
│   └── test_reference_costs.py      # TODO
├── docs/
│   ├── decisions.md                 # TODO
│   ├── model_review.md              # TODO
│   ├── meeting_notes.md             # TODO
│   ├── reference_registry.md        # TODO
│   └── team_roles.md                # TODO
└── presentation/
    ├── slides.*                     # TODO
    └── demo_instructions.md         # TODO
```

### 11.2 Conceptual API contracts (design plan; not existing code)

```python
# Loaded data are immutable or treated read-only during optimization.
instance = load_instance(path, fleet_policy=..., distance_policy=...)
assert check_instance(instance).ok

# Search settings are separate from the dataset.
config = load_solver_config(path_or_dict)

# The construction and optimization algorithm is our own module.
solution = solve_cvrp(instance, config)

# Independent validation of all hard constraints and the objective.
audit = validate_solution(instance, solution)
assert audit.feasible  # If not, do not report the result as successful.

# Persist evidence for every run, not just winner.
write_result_record(instance, config, solution, audit, provenance=...)
```

**API test:** swapping a benchmark file should alter instance quantities and outputs **without edits to `solve_cvrp` source**. `config` changes alter algorithm search behavior but never bypass mathematical constraints.

### 11.3 Example config skeleton (names are a **design proposal**, not current implementation)

```yaml
problem:
  instance_file: data/reference/example.vrp
  fleet_policy: at_most_k        # REQUIRES tutor confirmation
  max_vehicles_override: null    # never silently invent K
  distance_policy: benchmark_specific
  selected_customer_ids: null    # null = all input clients

solver:
  method: alns
  seed: 2026
  max_iterations: 100000        # illustrative; subject to tuning
  time_limit_seconds: 120       # illustrative; experiment budget must be approved
  max_no_improvement: 20000     # illustrative
  construction:
    method: randomized_insertion
    max_restarts: 20
  local_search:
    moves: [two_opt, relocate, swap, two_opt_star]
    candidate_neighbors: 30
    max_passes: 100
  alns:
    destroy_min_fraction: 0.05
    destroy_max_fraction: 0.30
    regret_k: 3
    reaction_factor: 0.1
    acceptance: simulated_annealing
    cooling_rate: 0.999
    restart_after_stagnation: 10000

experiment:
  run_seeds: [101, 102, 103, 104, 105]
  benchmark_manifest: data/benchmark_manifest.csv
  save_raw_runs: true
  output_dir: experiments
```

> Example numeric settings above are **configurable illustrations**, not promised optimal settings, accepted benchmark budgets or implementation claims. Each must be empirically tuned/approved, and values may depend on instance size.

### 11.4 Required run documentation

- [ ] Supported Python and OS versions, install commands, exact dependency versions and library licenses.
- [ ] Programmatic CLI/entry-point usage for arbitrary `.vrp` path and `K/Q` overrides where permitted.
- [ ] Example command for synthetic scenario generation.
- [ ] Commands for smoke tests, unit tests, 20+ benchmark batch and plot regeneration.
- [ ] Explanation of where actual `.vrp`/`.sol` data live and how they are obtained (with license/source).
- [ ] Explicit report of whether source `.vrp` files and reference `.sol` solutions are bundled or downloaded.
- [ ] Seed and hardware details, full config file, run ID, commit hash, timestamp and artifacts.
- [ ] Failure modes, numeric tolerance/rounding definitions, and exact final-output validator.
- [ ] Source and version references for every benchmark BKS/proven optimum.

---

## 12. Risk management and contingency plans

| Risk | Impact | Detection | Mitigation and owner |
|---|---|---|---|
| Fleet interpretation wrong (`<=K` vs `=K`) | Invalid ILP/benchmark | Tutor question or mismatched routes | **Blocker D01**, update all validators and experiments |
| Incorrect benchmark rounding | False gap conclusions | Published route-cost mismatch | Per-family cost audit, separate benchmark metrics |
| Loader silently assumes K | Invalid/unfair quality | Manifest/metadata mismatch | Explicit override or clear error, reviewer approval |
| Infeasible generated/loaded instance | Endless search or false success | Input checks, construction failure | Precheck, report `unknown` vs proven infeasible |
| Invalid moves return low cost | Artificially excellent gap | Independent validator | Test deltas, periodic full audit, hard fail invalid outputs |
| ALNS quality above grading warning | Grade cap risk | Per-instance gaps | Stronger neighborhoods, tuning, multistart, HGS baseline research |
| ALNS too slow for large n | Cannot meet realism goal | Scaling/memory profile | Incremental deltas, candidate lists, compilation, decomposition |
| Large dense matrices exhaust RAM | Crash or swap | Peak RSS, memory estimate | More compact weights, lazy/on-demand distances where valid |
| Too many hyperparameters overfit test | Misleading generalization | Tuning/test overlap | Freeze test manifest, tune on separate set |
| Only best seed presented | Biased robustness claim | Missing raw trials | Save all seeds, failures and descriptive statistics |
| External solver misrepresented | Academic-integrity issue | Code/doc review | Explicit authorship, tutor-approved role |
| Missing reference data/provenance | Gap cannot be defended | Absent manifest/source | Label unknown, retrieve legitimate source, no invented numbers |
| Time windows/traffic added midproject | Scope creep, failure of base results | Changed metrics/data models | Defer unless separately approved and after CVRP done |
| Experimental hardware changes | Unfair runtime comparison | Logs differ | Rerun matched hardware/budgets or prominently disclose |
| Notebook state dependence | Demo fails on fresh machine | Clean-run test | Modular code, pinned env, scriptable quick-demo |
| Deadline ambiguity | Missed submission | No confirmed dates | **D23** obtain official date/calendar |
| Charts without explanatory conclusions | Weak study despite many plots | Peer review | Every figure caption states hypothesis, observation and interpretation |
| Unsupported environmental claims | Misleading ADEME motivation | Claims without emissions data | Frame distance as proxy, qualify or estimate only with validated model |

---

## 13. Ownership, review workflow, and deadlines

### 13.1 Four-person suggested responsibility map (names: TBD by user)

| Role | Owns | Independent reviewer |
|---|---|---|
| Member A — mathematical modeling | ILP, NP-hardness proof, scope, tutor corrections | Member C |
| Member B — optimization | Construction, local search, ALNS, performance profiling | Member A |
| Member C — experiments | VRPLIB, validation suite, data manifest, 20+ runs, statistics | Member B |
| Member D — integration | Notebooks, README, reproducibility, plots, English slides/demo | Member C |

All four should understand the whole solver, contribute reviews/tests, and be capable of explaining the formal model and benchmark conclusions. **`[APPROVAL — USER]`** Assign actual names and availability.

### 13.2 Stage handoff protocol

1. Owner completes artifact and tests, adds linked evidence and raw logs.
2. Independent teammate reviews code, mathematics and numbers; records issues, not just “looks good.”
3. Reviewer checks a different instance/seed and reruns a representative test.
4. User approves scope/performance/time-budget decisions when flagged.
5. Tutor approves mathematical/academic decisions at mandated checkpoints.
6. Update README checkboxes, decision log, version and next milestone.

### 13.3 Scheduling requirements

The brief mentions:

- **Modeling checkpoint:** during Prosit 3; not graded but validated with tutor.
- **Project final notebook:** due **the day before oral defense**.
- **Oral defense:** **last day of the block**; in English, results/demo oriented.
- **ADEME application:** **12 July next** in the scenario text; without the course's confirmed year/date, do **not** put a guessed year in the actual project calendar.

**`[APPROVAL — USER + TUTOR]`** Fill in absolute dates (YYYY-MM-DD), intermediate review meetings, owner, venue/upload system and contingency buffer. Current date for this README: 2026-11-02; the assignment's relative “next July” cannot be interpreted as a formal school submission deadline without confirmation.

### 13.4 Template schedule to fill

| Milestone | Planned absolute date | Owner | Status |
|---|---|---|---|
| First tutor model review | TBD | Member A | Not approved |
| Revised modeling notebook | TBD | Member A | Pending review |
| Dataset manifest + parser tests | TBD | Member C | Not started |
| Construction + route validator | TBD | Members B/C | Not started |
| Local search + ALNS beta | TBD | Member B | Not started |
| Quality tuning and scaling tests | TBD | Members B/C | Not started |
| Frozen 20+ instance evaluation | TBD | Member C | Not started |
| Final notebook peer review | TBD | Member D | Not started |
| Notebook submission | TBD (day before defense) | Member D | Not started |
| English oral defense | TBD (last block day) | All | Not started |

---

## 14. Deliverable checklists

### Deliverable 1 — Modeling checkpoint (draft present; tutor not approved)

- [x] Context and formal CVRP graph/data.
- [x] Parameterized decision variables, objective and capacity/flow/depot/subtour constraints.
- [x] NP-hardness proof and worked examples.
- [x] Informative plots and references.
- [x] A-n32-k5 published reference-route validation.
- [ ] Independent mathematical and code checks.
- [ ] Clean environment rerun.
- [ ] Tutor approval and corrected final model.

### Final project — modeling and resolution

- [ ] Corrected complete ILP and explanation of exact-model role.
- [ ] Clearly justified and fully documented main metaheuristic.
- [ ] Readable, configurable Python solver that returns **valid solutions** on realistic instances.
- [ ] Explanation of construction, neighborhoods, iterations, adaptation and stop conditions.
- [ ] Demonstrations on multiple different instances.

### Final project — experimental analysis

- [ ] >=20 distinct benchmark instances loaded through `vrplib`.
- [ ] Consistent benchmark metrics and verified reference costs/status.
- [ ] Measured gap, time, feasibility, scalability, robust repeated trials.
- [ ] Statistical analyses, informative plots, parameter sensitivity and ablations.
- [ ] Clear limitations, weaknesses and realistic improvements.

### English defense

- [ ] Context and objectives before technical material.
- [ ] Prioritized results with appropriately labeled benchmark references.
- [ ] Small robust live demo showing configuration, routes and feasibility.
- [ ] Clear progress/risks/planning, division of roles and answered questions.

---

## 15. References and research tasks

### 15.1 Literature / verified technical starting points

1. **Dantzig & Ramser (1959)**, *The Truck Dispatching Problem*, Management Science. https://doi.org/10.1287/mnsc.6.1.80
2. **Clarke & Wright (1964)**, *Scheduling of Vehicles from a Central Depot to a Number of Delivery Points*, Operations Research. https://doi.org/10.1287/opre.12.4.568
3. **Miller, Tucker & Zemlin (1960)**, *Integer Programming Formulation of Traveling Salesman Problems*. https://doi.org/10.1145/321043.321046
4. **Toth & Vigo (2014)**, *Vehicle Routing: Problems, Methods, and Applications*, SIAM. https://doi.org/10.1137/1.9781611973594
5. **Uchoa et al. (2017)**, *New Benchmark Instances for the Capacitated Vehicle Routing Problem*, European Journal of Operational Research. https://doi.org/10.1016/j.ejor.2016.08.012
6. **Ropke & Pisinger (2006)**, *An Adaptive Large Neighborhood Search Heuristic for the Pickup and Delivery Problem with Time Windows*, Transportation Science. https://doi.org/10.1287/trsc.1050.0135 — ALNS framework **reference**; application differs from our basic CVRP.
7. **Vidal (2022)**, *Hybrid Genetic Search for the CVRP: Open-Source Implementation and SWAP* Neighborhood*, Computers & Operations Research. https://doi.org/10.1016/j.cor.2021.105643 — strong CVRP neighborhood/comparison reference.
8. **Wouda, Lan & Kool (2024)**, *PyVRP: A High-Performance VRP Solver Package*, INFORMS Journal on Computing. https://doi.org/10.1287/ijoc.2023.0055 — strong external solver reference.
9. **PyVRP/VRPLIB** official Python parser documentation: https://github.com/PyVRP/VRPLIB — note that `EUC_2D` may produce non-rounded distances; some benchmark families use integer-rounded reference costs.
10. **PyVRP** documentation: https://pyvrp.org/ and project repository https://github.com/PyVRP/PyVRP
11. **HGS-CVRP reference implementation** (Vidal): https://github.com/vidalt/HGS-CVRP — strong baseline / neighborhood research, with important reported limits for very large instances.
12. **CVRPLIB benchmark catalog:** https://galgos.inf.puc-rio.br/cvrplib/
13. **Project brief supplied by the team:** https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html# — confirm current official text, tutor interpretation and dates.

### 15.2 Open research checklist

- [ ] **[RESEARCH]** Select and justify construction heuristic(s) for homogeneous CVRP.
- [ ] **[RESEARCH]** Compare ALNS design variants, SWAP* and HGS evidence for quality/runtime.
- [ ] **[RESEARCH]** Verify per-family reference rounding and distance conventions before benchmarks.
- [ ] **[RESEARCH]** Verify `vrplib` behavior/version for each chosen dataset file, including sparse/explicit matrix limitations.
- [ ] **[RESEARCH]** Evaluate numerical stability/scaling for large matrix costs and incremental deltas.
- [ ] **[RESEARCH]** Identify published references and distinguish certified optima vs BKS.
- [ ] **[RESEARCH]** Identify several-thousand-client datasets or generate explicitly labeled realistic synthetic tests.
- [ ] **[RESEARCH]** Determine whether tutor permits Numba/external implementation/baseline solvers and proper citations.
- [ ] **[RESEARCH]** Study variance/timing methodology and fair per-run comparison protocols.
- [ ] **[RESEARCH]** Record exact algorithm versions and benchmark source retrieval dates at evaluation time.
- [ ] **[RESEARCH]** Assess appropriate emission interpretation in ADEME narrative without confusing it with objective proof.

---

## 16. Immediate next actions and decision log

### 16.1 The next ten actions, in order

1. **[ ] [BLOCKER]** User + tutor decide **fleet rule** (`K` maximum vs exactly `K` active) and static **distance objective**.
2. **[ ]** Perform fresh clean-run of existing 68-cell modeling notebook and record environment/results.
3. **[ ]** Independently audit ILP and MTZ proof using edge-case scenarios and, optionally, tiny exhaustive/ILP cross-checks.
4. **[ ] [APPROVAL — TUTOR]** Complete the first model review, capture feedback, and update the “corrected PLNE.”
5. **[ ] [APPROVAL — TUTOR]** Confirm algorithm originality/external solver allowance, primary metaheuristic and official 20+ dataset rules.
6. **[ ]** Create the project source/data/test/config structure and single canonical instance/solution schema.
7. **[ ]** Implement general `vrplib` loading, source ID mapping, cost policy and reference cost audit.
8. **[ ]** Implement independent full solution validator with tests, then initial route construction.
9. **[ ]** Implement local search and ALNS incrementally, verify deltas/feasibility, profile runtime.
10. **[ ]** Freeze experiment protocol, run 20+ distinct instances with repeated seeds, analyze, consolidate notebook and prepare English presentation.

### 16.2 Decision log (must be maintained continuously)

| Date | ID | Proposal / evidence | Decision | Approved by | Implementation impact |
|---|---|---|---|---|---|
| 2026-11-02 | Scope | Basic CVRP, no time windows or time-dependent traffic | User chose CVRP-only | User (prior requests) | Advanced variants deferred |
| 2026-11-02 | Objective | Distance for VRPLIB compatibility | User chose distance | User (prior request) | Objective static distance; tutor approval still pending |
| 2026-11-02 | Data | Both synthetic and real VRPLIB examples | User chose both | User (prior request) | Existing notebook contains both |
| 2026-11-02 | Code scope | Modeling plots/validation only, no optimizer in first checkpoint | User chose this scope | User (prior request) | Modeling notebook only |
| TBD | D01 | `at_most_k` is current modeling assumption | **Pending** | Tutor | Could require revised ILP/validator |
| TBD | D07 | Own ALNS with separate external baseline | **Pending** | Tutor | Algorithm architecture/audit |
| TBD | D23 | Actual final dates and scope of July wording | **Pending** | Tutor/user | Schedule/submission |

### 16.3 Final non-negotiable statements

- **Never hard-code instance-specific values in the solver**. Every fleet size, capacity, customer count, demand, depot location, coordinates and travel costs come from a validated instance/configuration; all meaningful metaheuristic/test parameters are configurable too.
- **Never claim to have optimized a published benchmark merely by loading its reference solution.**
- **Never report an infeasible route as a successful optimization result.**
- **Never equate a BKS reference with proven optimality without proof.**
- **Never mix rounding conventions, vehicle-count rules or cost units in a gap comparison.**
- **Never promise exact global optimality for thousands of customers from a heuristic.** Aim for strong, measured, reproducible quality with honestly reported computational cost.
- **Never start the next unapproved scope change silently.** Mark research decisions and obtain the specified user/tutor acceptance.
- **Never treat “19 modeling plots” or “one reference route demonstration” as the required 20-instance solver benchmark.**

**Next gate:** finish Phase 0 tutor approval, then complete independent evaluator and a mandatory **algorithm-selection prototype (Gate A0 in §17)** before locking the main optimizer. The optimization algorithm itself remains **TODO**.

---

## 17. Critical algorithm-quality audit and implementation gates

**Audit date:** 2026-11-02. **Status:** plan reviewed, **not** an implemented or benchmarked optimizer. **Do not** mark any tasks below complete until evidence is produced. The original plan was substantial but its early ALNS commitment was not supported by comparative experimental evidence. This section is mandatory and overrides any conflicting, provisional recommendation above.

### 17.1 Corrections and risks found in the previous plan

| Severity | Defect or risk | Required action / acceptance evidence |
|---|---|---|
| **CRITICAL** | Main ALNS architecture selected before evidence that its quality is competitive | **A0 algorithm-selection gate**: own ALNS prototype vs own ILS+strong local search, measured against independent HGS-CVRP and modern PyVRP references, if tutor permits; decide with disjoint development instances and fixed budgets. |
| **CRITICAL** | “Works” / “improves baseline” is weaker than an explicit solution-quality target | Add formal per-instance gap / feasibility / runtime targets and **redesign triggers**; see §17.3. No invented claim of guaranteed optimality. |
| **CRITICAL** | A single flawed or unavailable construction heuristic can abort feasible instances | Implement multiple starts and capacity-aware insertion; include a dedicated **feasibility recovery strategy**. Never call heuristic failure proof of infeasibility. |
| **CRITICAL** | Rounding and fleet metadata errors can make all gap comparisons wrong | Validate reference-route objective, fleet policy, node-ID mapping, benchmark family and distance scaling **before** evaluating any heuristic. |
| **HIGH** | SWAP*, cross-exchange, sequence relocation and ejection-chain style repair were treated as largely optional without an evidence-based quality gate | Make a **strong CVRP neighborhood suite** a required candidate set; only omit an operator if ablation evidence justifies omission. |
| **HIGH** | Search feasibility is oversimplified | Decide whether intermediate infeasible solutions are forbidden or permitted under controlled penalties. Even if allowed, the **best output must be strictly feasible** and validated independently. |
| **HIGH** | Unbounded configuration combinations invite overfitting and bugs | Split settings into **required / experimentally tunable / experimental feature flags**; validate parameter interactions and defaults, tune only on a separate development set. |
| **HIGH** | Thousands-customer claims could outpace tested performance | Define explicit size/CPU/RAM acceptance runs; quantify both memory and solution quality; standard HGS-CVRP is documented as not directly targeted to >5,000 customers. |
| **HIGH** | The earlier README called modern PyVRP a “hybrid genetic search” | Corrected: PyVRP 0.13+ switched from HGS to **Iterated Local Search (ILS)**; Vidal's separate HGS-CVRP remains HGS. Pin exact versions and compare algorithms by **version**, not brand. |
| **HIGH** | Algorithm or cost-delta bugs may silently improve cost by violating constraints | Property-based tests, independent full evaluator, route-invariant tests, metamorphic tests, small exhaustive cross-checks, periodic audits, and export/reload audits are mandatory. |
| **MEDIUM** | All neighborhoods were promised for asymmetric/non-metric costs without clear delta proof | Either fully support them with tested reversal/arc costs, or mark unsupported datasets explicitly. **Standard symmetric CVRP** should be correct and fast before expanding. |
| **MEDIUM** | Academic originality vs third-party solver use is unresolved | Obtain tutor answer: external solvers as **independent baselines only** until explicitly permitted otherwise. Maintain attribution and proof of own contribution. |

### 17.2 A0: mandatory empirical algorithm selection **before locking the main solver**

**Do not assume ALNS is better than ILS or HGS.** Strong external implementations are useful **references**, but are not our own code. The first prototypes may be deliberately small/limited; comparisons are used to decide development effort, not to claim a fair final leaderboard prematurely.

- [ ] **[APPROVAL — TUTOR]** Confirm requirements for original implementation, allowed libraries, compiled/Numba/C++ acceleration and external comparisons.
- [ ] Pick a **development-only** (non-final-test) set of **6–10 varied CVRP instances** covering at least two scales, geographic patterns and load tightness. A separate final set still must have **20+ distinct** benchmarks.
- [ ] Build the **common independent evaluator and cost adapter first**; all algorithms must consume the *same* validated `CVRPInstance` and satisfy the same fleet rule.
- [ ] Prototype a **strong local-search ILS**: construction → perturbation (e.g., double bridge, ejection-chain-like changes, route exchange) → local search → acceptance/restart.
- [ ] Prototype **ALNS**: multiple removal/repair methods, adaptive selection, calibrated acceptance, strong local search; do not compare a full ALNS to a deliberately handicapped ILS.
- [ ] If tutor permits, run separate **PyVRP ILS** and **HGS-CVRP** versions as independent reference baselines. Do not call them student-made or reuse their returned reference routes to seed our main benchmark.
- [ ] Use **identical verified costs, K policy, instance inputs** and predeclared per-instance elapsed-time budgets. Report language/compiled-core differences, CPU threads and preprocessing; perfect cross-language fairness is impossible, so be transparent.
- [ ] Record **best/mean/worst feasible gap**, feasibility rate, time-to-first-feasible, improvement over construction, runtime, peak RSS, and quality-versus-time traces. Use several seeds; a one-seed win does not determine architecture.
- [ ] Choose the **own-implementation primary algorithm** based on observed quality and achievable development time. Possibilities: robust ALNS+LS; ILS+LS; or **own HGS-inspired method** if ALNS/ILS are inadequate and full originality requirements are satisfied.
- [ ] Save the selection record (`docs/algorithm_selection.md`): choices, rejected candidates, actual data, original code status, version, author/tutor approval and reason.

**Gate A0 exit:** signed selection record based on validated measurements, **not** a literature assumption or the attractiveness of an acronym. Algorithm decision D08 remains **pending** until completed.

### 17.3 Measurable quality gates and mandatory reaction when results are weak

**All thresholds are proposals for user approval, not facts about achieved performance.** A threshold above the marking cap does not make a failed solution acceptable. Distinguish targets from guaranteed outcomes and apply targets separately by instance size/time budget.

| Gate | Proposed target / interpretation | Response if not met |
|---|---|---|
| **F0: correctness** | **100% of reported successful solutions** pass independent coverage, depot, capacity, fleet and objective checks | Stop: fix bug; any invalid incumbent is unusable. |
| **F1: baseline improvement** | On the predeclared development set, primary method improves construction-only **mean** gap at matched budget; document exceptions | Profile neighborhoods and construction; check acceptance and candidate lists. |
| **F2: benchmark quality** | Aim for **mean BKS gap ≤3%** on the final test set (ambitious proposal) and identify any instance with gap **>7%** for mandatory diagnosis; **no guaranteed result** | Trigger enhanced local search / adaptive tuning / alternative architecture. Do not tune on the held-out test set and then describe it as untouched. |
| **F3: reliability** | On a confirmed-feasible benchmark test set, target **100% final feasible results** within the declared budgets; log all failures | Introduce feasibility-preserving construction and repair, additional restarts/feasibility-focused logic. |
| **F4: scalability** | Demonstrate actual results at 100/500/1,000 and, if feasible and available, 2,000+ customers with predeclared RAM/time budgets; avoid promises for untested scales | Profile and simplify search, candidate neighborhood and matrix memory; consider decomposition/compiled hotspots. |
| **F5: statistical credibility** | Freeze test instances/seeds/config, publish **all** runs, including timeouts and invalid outputs, and report best/mean/std/worst and uncertainty | Rerun fair paired experiments; eliminate selective reporting. |

**Decision triggers** (apply to *development* experiments, not hidden tuning on final test):

1. If an initial feasible solution often fails: prioritize **capacity-compatible assignment, route elimination/reinsertion, regret repair, ejection chains/temporary infeasibility**, and perhaps small feasibility MILP/CP-SAT fallback where academically permitted.
2. If routes are feasible but gap stays high: diagnose cost rounding, fleet semantics and operator math; then strengthen **inter-route moves, SWAP*, 2-opt*, Or-opt, cross-exchange**, perturbation and diversification. Try ILS/HGS-inspired design if warranted.
3. If gap improves but runtime is excessive: run profiler, use incremental Δ-cost and Δ-load updates, granular neighbor lists, selective local search, Numba or compiled hotspots if approved; measure quality loss from acceleration.
4. If large instances run out of memory: remove dense temporary matrices and redundant caches, use appropriate integer representations, reduce trace retention, and research decomposition/candidate-only storage. Profile rather than assume the fix helps.
5. If tuning wins only on selected benchmarks: stop, check for overfitting, revise the development split, re-freeze the evaluation procedure; report exploratory runs separately.

### 17.4 Minimum competitive neighborhood and diversification specification

- [ ] Intra-route **2-opt** and **Or-opt** (configurable segment length) with correct handling of return-to-depot legs.
- [ ] Inter-route relocate, swap and **2-opt\*** (route tail exchanges), including empty/singleton route corner cases.
- [ ] **SWAP\*** candidate implementation or explicitly documented failed/budgeted investigation; evaluate whether its improvement pays for runtime.
- [ ] Route-level **ruin-and-recreate** capable of removing entire routes, not only isolated customers, with **regret-k** and best-feasible insertion; controlled randomization.
- [ ] Periodic **diversification** that is genuinely different from repeating the same local optimum (multi-start, guided perturbation or adaptive removal).
- [ ] **Intensification** on elite solutions and stagnation logic; log actual improvement rate, not just iteration counts.
- [ ] Candidate neighborhood restriction must have a documented **escape/fallback strategy** (occasional wider search, route-level moves, or full-scan verification for small cases); otherwise fast search can exclude critical improving moves.
- [ ] Strictly specify how temporary infeasibility is handled: feasible-only or **penalized infeasible intermediate**, with load violation penalties, penalty adaptation rules, and a hard independent validator for final output.
- [ ] Verify every neighborhood operator's exact Δcost formula on randomized tiny symmetric and asymmetric instances against full objective recomputation; add inverse/permutation tests.
- [ ] Define search-state ownership and caching: route updates must invalidate relevant prefix loads/cost caches and neighbor data, and never mutate `best_solution` by aliasing.

**Important:** having a setting called `enable_swap_star` without tested code is *not* implementing SWAP*. Every exposed parameter must have an effect, input validation and a reproducible test.

### 17.5 Benchmark validity and completeness gates

- [ ] Build a **family-specific distance/rounding rule registry**. `vrplib` can return raw Euclidean costs for `EUC_2D` even where published X-set BKS uses rounded integers. Neither `np.round` nor `floor(x+0.5)` is automatically correct for all families. Distinguish `EXPLICIT`, `CEIL_2D`, and scaled formats; preserve directional arcs when applicable. See official VRPLIB documentation and PyVRP `read(..., round_func=...)`.
- [ ] Recalculate the **published routes of at least one instance per family**, and preferably all available reference routes, and require exact matching cost where the benchmark uses integer units. **No pass => no gap.**
- [ ] Do not trust `-kNN` string parsing as a universal meaning; determine whether `K` is available trucks, optimum route count, lower-bound hint or simply family notation. Record approved fleet rule per instance.
- [ ] Verify that loader, validator, optimizer, `.sol` export, `.sol` import and plot all agree on **original IDs / internal 0-based IDs / depot mapping**. Include tests where original node labels are not contiguous or depot first.
- [ ] Distinguish **proven optimum / BKS / lower bound** and date of reference. Negative BKS gaps are a **verification event**, not immediate proof of a new record.
- [ ] Compute objective in **the same units** as benchmark (often abstract distance units, not km); verify direct/return edges, any distance scaling, and prohibition of extra depot visits if model assumes one tour per vehicle.
- [ ] Use **≥20 final distinct** benchmarks with independent repeated seeds. Synthetic stress tests are additional; test instances cannot be repurposed as tuning data without explicitly disclosing that the result is exploratory.
- [ ] For an optional exact MILP, report solver **status and bound**, not merely the best feasible incumbent as an optimum. Formally valid bounds must use the same objective and instance assumptions.

### 17.6 Additional professor-defensible correctness and complexity tests

- [ ] Construct tiny benchmarks (`n≤8` if tractable) where **exhaustive search or small exact MILP** obtains a certified optimum; compare heuristic output and validator, including cases where optimal routes use fewer than `K` vehicles.
- [ ] **Metamorphic tests:** relabel all customers and permute the matrix consistently => identical cost for corresponding route; multiply every distance by positive scalar => scaled cost; increase `Q` or `K` under at-most-K => existing feasible plan remains feasible; reverse route under **symmetric** matrix => equal cost, but **not** generally under asymmetric matrix.
- [ ] Test zero-demand mandatory customers, duplicate coordinates, zero-cost arcs, exactly-full truck, one customer, `K>n`, bin-packing-infeasible but aggregate-demand-feasible instance, all-zero costs and unsupported distance formats.
- [ ] Check **integer distance arithmetic** on integer-weight benchmarks to avoid float drift; if using floating cost, set defensible tolerance. Save computed objective and validated objective in run record; require matching within the prescribed tolerance.
- [ ] Document realistic algorithmic complexity: a complete three-index ILP has O(K n²) binary arc variables, while naive large-neighborhood scans and regret insertions can be expensive; report **actual** profiled cost per iteration and memory growth (including allocations beyond the base distance matrix).
- [ ] Explain why **finding a feasible solution** is different from proving existence; NP-hard bin-packing-style allocation may defeat a greedy constructor even if a CVRP solution exists.
- [ ] Include proof/explanation of correctness and feasibility invariants for each move, not just tests and plots; explicitly identify any assumptions behind O(1) deltas (symmetric matrix, fixed depot, etc.).
- [ ] Create a **staged-release table**: small exact-optimum tests, medium development suite, held-out 20+ benchmark suite, 1k/2k+ scalability suite. Do not infer reliability of the entire distribution from a few easy examples.
- [ ] Write down the distinct difference between **distance minimization** (graded VRPLIB objective), original story's **duration minimization**, and any future traffic/emissions goals. Confirm tutor approval; no unvalidated CO₂-saving percentages.

### 17.7 Explicit ownership and approvals for this audit

- **`[APPROVAL — USER]`** Accept revised algorithm-selection process and proposed performance thresholds (especially exploratory 3% mean BKS target, 7% diagnosis trigger and budgets). These are goals, not guaranteed outcomes.
- **`[APPROVAL — TUTOR]`** Confirm whether primary metaheuristic may change from ALNS to ILS/HGS-inspired and whether C++/Numba/third-party solvers are permitted in a graded implementation.
- **`[RESEARCH]`** Pin version and historical algorithm of PyVRP (current versions ILS), HGS-CVRP and vrplib; pin exact benchmark convention/source/version, and cite scholarly references where applicable.
- **`[BLOCKER]`** No official gaps until distance/ID/fleet/solution cost reference validation passes.
- **`[BLOCKER]`** No claim of competitive solution quality until actual, independently validated repeated benchmark results exist.
- **`[BLOCKER]`** No statement that global optimality is guaranteed unless a matching exact solver **proves** it for the particular instance.

**Technical references verified for this audit:**

- PyVRP 0.13+ release notes (HGS to ILS): https://github.com/PyVRP/PyVRP/releases
- PyVRP ILS implementation: https://pyvrp.org/notebooks/pyvrp_implementation.html
- PyVRP benchmarking methodology: https://pyvrp.org/dev/benchmarking.html
- Vidal HGS-CVRP design and scope: https://github.com/vidalt/HGS-CVRP
- VRPLIB parsing and rounding behavior: https://github.com/PyVRP/VRPLIB

**Hard conclusion:** The project remains at **mathematical modeling draft**. Sections 17.2–17.6 are **implementation/research/experiment TODOs**, not completed work. The next engineering milestone is a tested independent data/cost/feasibility core followed by the A0 algorithm-selection pilot.
