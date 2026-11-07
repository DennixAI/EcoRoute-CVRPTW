# EcoRoute-CVRP — Advanced TD-CVRPTW specification and project context

> **Latest user decision, 2026-11-07:** target time-dependent capacitated vehicle routing with time windows (TD-CVRPTW). This supersedes the earlier CVRP-only selection. This document specifies future work; the existing notebook remains a classical CVRP draft. No advanced solver, advanced notebook implementation, experiments or tutor approval is established.

## Advanced specification navigation

- [Scope and authority](#a1-scope-and-authority)
- [Temporal formulation](#a2-temporal-formulation)
- [Traffic and paths](#a3-traffic-and-paths)
- [Exact discrete formulation](#a4-exact-discrete-formulation)
- [Configuration contract](#a5-configuration-contract)
- [Experiments and figures](#a6-experiments-and-figures)
- [Engineering and validation](#a7-engineering-and-validation)
- [Status, decisions and next steps](#a8-status-decisions-and-next-steps)

## A1. Scope and authority

Official requirements come from the French assignment in [sources.md](sources.md). The latest user decision chooses the team's scope; actual files establish implementation status, recorded tutor feedback establishes review status, and earlier assistant proposals remain recommendations. The live CESI URL was attempted on 2026-11-07 but could not be retrieved by the web reader; no claim of independent confirmation of the live text is made.

| Layer | Problem and objective | Role |
|---|---|---|
| 1 | Classical CVRP; minimize static total distance | Existing modeling foundation and reference benchmark |
| 2 | CVRPTW; capacity, service windows, service durations and waiting | Official Level A advanced variant; future implementation |
| 3 | TD-CVRPTW; Layer 2 plus predicted time-dependent road traffic; minimize total route elapsed time | Latest user-selected final target; future implementation |

Level B names CVRP; Level A names CVRPTW. Predicted traffic appears separately in the original narrative. Their combination is our selected scope, not an assertion that CESI explicitly names TD-CVRPTW as mandatory Level A. The source's traffic sentence is traceable in the original statement in `sources.md`.

Current assumptions: one depot; configurable fleet; identical capacities within each instance; known nonnegative unsplit demands; every required customer served once; each active truck makes one connected depot-returning route. At most K is the working fleet convention, pending tutor/benchmark confirmation. Exactly K requires nonempty routes and a separate policy. Directed roads and asymmetric travel are permitted. Zero-demand customers remain mandatory. Forecasts are deterministic inputs known at planning time; live dispatch, stochastic demand, multi-depot routing, heterogeneous capacities and carbon optimization are separate research extensions.

The prior user-approved CVRP-only and distance choices applied to the first notebook and remain historical records in Section 14. They no longer restrict the final project to Layer 1. Baseline equations M1–M8 in Section 6 remain applicable to all layers' routing structure; their distance objective applies to Layer 1 only.

## A2. Temporal formulation

This is a continuous-time mathematical specification for future implementation and review, not a claim of a linear program. Let C, V, F, A, q, Q, x, y, z, u retain Section 6 definitions. Use coordinate symbols p_i=(X_i,Y_i), reserving a_i,b_i for time bounds. All times are nonnegative minutes from a declared planning epoch; all durations use minutes. H is a finite horizon, 0≤a_i≤b_i≤H, s_i≥0. Depot departure bounds are E_k≤L_k≤H, and latest return is B_k≤H. Depot loading is outside route time unless explicitly represented in the input convention.

| Symbol | Definition/domain | Purpose |
|---|---|---|
| a_i,b_i | Opening and latest service-start time | Hard customer window under the provisional start policy |
| s_i,q_i | Service duration and demand | Time and capacity data |
| E_k,L_k,B_k,H | Earliest/latest departure, latest return, horizon | Scheduling limits |
| tau_ij(t), F_ij(t)=t+tau_ij(t) | Travel duration and arrival map at departure t | Time-dependent travel input/oracle |
| A_ik,S_ik | Arrival and service-start times, continuous in [0,H] when assigned | Distinguish physical arrival from service |
| C_ik=S_ik+s_i y_ik | Service completion, derived | No independent completion decision |
| D_ik=C_ik | Customer departure, derived | No post-service holding under this provisional policy |
| W_ik=S_ik−A_ik | Waiting before service, derived, nonnegative | Includes optional pre-service holding |
| T_k,R_k | Depot departure and return, continuous in [0,H] | Route scheduling decisions |
| delta_k=R_k−T_k | Elapsed route time, derived | Primary objective contribution |

Retain M1–M8 and binary domains, and strengthen activation explicitly with y_ik≤z_k. The original MTZ remains necessary when travel/service can be zero; temporal inequalities alone must not be assumed to exclude all subtours. The following equations use implications with binary antecedents, interpreted logically; arbitrary nonlinear indicator expressions are not claimed to be solver-supported MILP constraints.

| Equation | Rule (for all relevant i,j,k) | Meaning |
|---|---|---|
| T1 | 0≤A_ik,S_ik,D_ik≤H y_ik; S_ik≥A_ik | Unassigned customers have zero schedule; no negative waiting |
| T2 | a_i y_ik≤S_ik≤b_i y_ik; D_ik=S_ik+s_i y_ik | Service-start windows, full service duration |
| T3 | E_k z_k≤T_k≤L_k z_k; T_k≤R_k≤B_k z_k | Inactive trucks have T=R=0; active depot limits |
| T4 | x_0jk=1 implies A_jk=F_0j(T_k) | Actual arrival from depot |
| T5 | x_ijk=1 implies A_jk=F_ij(D_ik), i,j∈C | Exact chronological propagation |
| T6 | x_i0k=1 implies R_k=F_i0(D_ik) | Actual return to depot |
| T7 | min Σ_k(R_k−T_k) | Primary advanced objective |

Service windows provisionally constrain commencement. If the tutor/data require completion within the window, replace S_ik≤b_i y_ik by D_ik≤b_i y_ik. Do not apply both interpretations under a single undocumented flag. Example: arrival 09:30, window 10:00–12:00, service 20 minutes → wait 30, start 10:00, depart 10:20. Arrival 12:01 is infeasible. Starting at 11:50 and ending 12:10 satisfies a start window and violates a completion window.

S may exceed max(A,a): deliberate pre-service holding is allowed. This is important when departure timing can improve route elapsed time. The special earliest-service policy S=max(A,a) is useful as a feasible schedule constructor, but is not assumed to optimize the full model. For fixed route order and departure, FIFO plus earliest service can test hard-window feasibility; minimizing elapsed time with flexible departure/holding requires a separate schedule optimization step. No path-side discretionary waiting is assumed in the initial positive-speed FIFO model.

Report driving Σ tau on selected scheduled legs, waiting Σ W, service Σ s, route elapsed Σ delta, makespan max R, used fleet Σ z and traveled road distance separately. Under the selected no-post-service-holding convention, elapsed=driving+waiting+service on each active route. Total service is constant when all customers are mandatory, but remains part of elapsed time. Minimizing pure driving can favor more waiting; minimizing makespan optimizes the latest absolute return; neither is equivalent to minimizing total elapsed time. Flexible departures can reduce time spent waiting at customers; report departures and any depot holding outside elapsed time. T7 is a project proposal aligned with tour-duration wording, pending tutor agreement. Distance and vehicle count are reported metrics; lexicographic tie-breaks require an explicit policy, never an arbitrary weighted mixture or a change to a published objective.

## A3. Traffic and paths

Let the directed road network be G_R=(N_R,E_R). Map each stop to a road vertex with explicit connector costs. Each segment e has length ell_e>0 and a predicted speed profile v_e(t)>0 over contiguous forecast intervals spanning [0,H]. Units are length/minute. Profiles are exogenous; trucks do not change traffic. Missing intervals, unknown directions, negative/nonfinite speed, unmapped stops and horizon overrun cause an explicit data error or unavailable traversal. No real forecast dataset is currently bundled. Generated peaks, off-peak periods and incidents must be labeled synthetic with generator, seed and provenance.

For segment entry t, define exit F_e(t) by:

$$\int_t^{F_e(t)} v_e(r)\,dr=\ell_e.\tag{TR1}$$

For piecewise-constant speeds, consume distance up to each interval boundary, then continue at the next interval's speed until the segment is complete. A synthetic example: 10 km, departure 07:55, speed 60 km/h until 08:00 then 30 km/h → 5 km in five minutes and 5 km in ten more; arrival 08:10. Freezing the entry speed would incorrectly predict 08:05. These are explanatory invented values, not forecasts.

Positive speed integration yields a nondecreasing segment arrival map (FIFO). Compose these maps along a path. A time-dependent earliest-arrival shortest-path oracle chooses a path for each stop pair and departure; tau_ij(t)=earliest_arrival_ij(t)−t. Store its path and distance so temporal and distance metrics refer to the same physical path. Static straight-line distance is not traffic. Passing another customer's road location is transit, not service. When the earliest-arrival path changes, secondary distance is the selected path's length, not a fixed distance matrix. Deterministic path ties use a disclosed tie-break.

Initial recommendation: time-dependent shortest-path evaluation under FIFO with positive integrated speeds; fixed paths are a labeled comparison approximation. Closures and zero speeds require an explicit entry/in-progress traversal and waiting policy before support; the first implementation should reject them. Never silently substitute a free-flow speed or extrapolate beyond the forecast horizon. A later imputation policy must record its source, uncertainty and effect on feasibility.

Direct piecewise-constant durations tau(t) can violate FIFO at boundaries: check t1+tau(t1)≤t2+tau(t2) for t1<t2. Prefer speed integration over arbitrary duration steps. Piecewise-linear arrival maps may represent integrated speeds; interpolation needs monotonicity checks and approximation-error accounting, especially near windows. Caches must include departure (or an error-certified time cell), forecast version, direction, scenario and path policy. Coarse caching cannot turn a late arrival into a feasible one.

## A4. Exact discrete formulation

First exact reference recommendation: a time-indexed arc model for tiny finite-horizon instances. It is exact for the declared discrete model, not automatically for the continuous road process. This favors explainability and explicit activation over an unproved linearization of tau(D). Retain the continuous evaluator in A2–A3 as the practical heuristic specification.

Choose tick Delta>0 minutes, integer h=H/Delta, and grid times 0,…,h. Scale q,Q without changing demand semantics. Round opening/earliest-departure times up; latest-start/latest-departure/latest-return times down; service and evaluated travel arrivals up. State the conservative rounding policy in the manifest. Earliest arrival f_ij(t) is a precomputed integer tick from the road oracle for grid departure t, or unavailable; f_ij(t)≥t. Build it only for departures with arrival inside the horizon. If using a completion window, use conservatively rounded service in that bound too. A continuous-feasible plan may disappear on a coarse grid; a grid optimum is not a continuous optimum. Revalidate grid solutions against original continuous travel and compare multiple resolutions.

For every valid (i,j,t,k), introduce binary X_ijtk indicating departure along arc i→j at grid tick t. Keep x_ijk=Σ_t X_ijtk and all M1–M8; disallow arcs whose departure/arrival cannot meet horizon bounds. The integer schedule variables A,S,D,T,R have the bounds from T1–T3 expressed in ticks. The complete additional linear equations are:

$$x_{ijk}=\sum_{t:(i,j,t)\ valid}X_{ijtk}.\tag{D1}$$
$$D_{ik}=\sum_{j,t}tX_{ijtk},\quad
A_{ik}=\sum_{j,t}f_{ji}(t)X_{jitk}\qquad(i\in C).\tag{D2}$$
$$S_{ik}\ge A_{ik},\quad D_{ik}=S_{ik}+\hat s_i y_{ik},\quad
\hat a_i y_{ik}\le S_{ik}\le\hat b_i y_{ik}.\tag{D3}$$
$$T_k=\sum_{j\in C,t}tX_{0jtk},\quad R_k=\sum_{i\in C,t}f_{i0}(t)X_{i0tk}.\tag{D4}$$
$$\hat E_k z_k\le T_k\le\hat L_k z_k,\quad T_k\le R_k\le\hat B_k z_k,\quad y_{ik}\le z_k.\tag{D5}$$
$$\min\ \Delta\sum_k(R_k-T_k),\quad X,x,y,z\ binary,\ A,S,D,T,R\ integer\ in\ [0,h].\tag{D6}$$

All customer sums in D2 cover permitted predecessor/successor stops and their valid ticks. M2/M3 ensure exactly one selected outgoing/incoming time arc for an assigned customer, so these sums select its actual departure and arrival. Unassigned variables are zero by D2–D3; inactive depot schedules are zero by D4–D5. Preserve MTZ even with zero-time arcs; use integer u if the final PLNE is required to be all-integer. D1–D6 plus M1–M8 and domains are the complete discrete reference formulation. In Layer 2 use constant travel times in f; in Layer 1 remove the scheduling restrictions and use the distance objective. A Layer 1 comparison must not inherit restrictive advanced windows.

No temporal big-M is needed here. The existing MTZ M=n+1 remains justified by 0≤u≤n. For future piecewise-linear formulations, choose a segment with binaries and enforce exact affine arrival on the selected segment; bound all times and derive each deactivation constant from expression extrema. For an arrival variable in [0,H] and a candidate arrival expression in [0,H+tau_max], an equality can be relaxed using M=H+tau_max (or tighter directional bounds). If no finite bound exists, this M is invalid. Indicator syntax for an arbitrary nonlinear oracle does not make it MILP. A piecewise-linear formulation is a research alternative, not implemented or claimed complete here.

TSP reduces to Layer 3 by one sufficient-capacity truck, zero service, broad windows, fixed departure 0 and constant travel durations equal to TSP edge costs with a polynomially encoded sufficient horizon. Then T7 equals TSP tour cost, so optimization remains NP-hard. Decision NP-completeness is justified for the finite explicit discrete/rational polynomially verifiable variant; no blanket NP-membership claim is made for arbitrary travel oracles. Time-indexed size is O(K n² h), pseudo-polynomial in encoded horizon and potentially huge. At n=1000, K=20, h=1440 it is already tens of billions of potential X variables. It is a correctness reference, not the thousands-customer solution architecture.

## A5. Configuration contract

Everything below is a **planned interface**, including advanced fields; none is implemented by adding this table. Section 7 preserves existing Layer 1 example settings. Canonical immutable instance data and forecast provenance are separate from search/experiment configuration. Fields sharing a row have the stated validation/default policy individually; no silent defaults for required Layer 3 data.

| Field | Meaning; type and units | Valid range / source | Default policy and validation |
|---|---|---|---|
| `time_windows` | Array n×2 of a,b; minutes | 0≤a≤b≤H; dataset/synthetic generator | Required; preserve start/completion semantics |
| `service_durations` | Array n, minutes | finite ≥0; dataset | Required; zero only if explicitly supplied |
| `customer_demands` | Array n, capacity units | 0≤q≤Q; dataset | Required; ID alignment, no split |
| `vehicle_count` | Integer K | ≥1, or zero for agreed empty case; metadata/override | Required; never infer universal upper bound from filename |
| `vehicle_capacity` | Numeric Q, demand units | finite >0; dataset | Required, common within instance |
| `fleet_rule` | Enum at_most_k/exactly_k | benchmark/tutor policy | Working at_most_k; reject unknown benchmark convention |
| `depot_time_window` | Departure and return bounds; minutes | within H; dataset/config | Required; distinguish departure closing from latest return |
| `time_horizon` | Numeric H, minutes | finite >0; dataset/config | Required; forecast covers all evaluated travel |
| `vehicle_departure_policy` | Enum fixed/flexible; per-vehicle bounds | instance contract | Explicit; fixed means E=L |
| `earliest_departure`, `latest_departure`, `latest_return` | Scalars or K arrays, minutes | 0≤E≤L≤B≤H | Required; dimension validation |
| `window_policy` | Enum service_start/service_completion | source/tutor | Provisional service_start; always log |
| `holding_policy` | Enum pre_service/earliest_service | model policy | Pre-service holding allowed; constructor may use earliest |
| `time_reference`, `time_zone` | Epoch/date and IANA zone | dataset metadata | Required; convert to monotonic elapsed minutes; reject ambiguous DST clock values without offset |
| `road_network` | Directed vertices/segments and stop mapping | road source or labeled synthetic | Required Layer 3; reachability/connectors validated |
| `road_distance` | Segment lengths; numeric array, declared length units | finite >0; road data | Required; no geographic degrees treated as length |
| `traffic_profiles` | Segment×interval speeds, length/minute | finite >0, contiguous coverage; forecast/generator | Required; missing data rejected |
| `traffic_interval_minutes` | Numeric or vector of interval widths | >0; forecast metadata | Required; boundaries increasing and cover H |
| `traffic_prediction_source` | Provider/version/retrieval/issue time and license | provenance record | Required; synthetic explicitly named |
| `traffic_scenario` | Scenario ID and immutable profile hash | manifest | Required; no cross-scenario gap |
| `travel_time_policy` | Enum integrated_speed/fixed_path_approximation | model configuration | integrated_speed recommended; flag approximations |
| `time_dependent_travel_time` | Callable/oracle descriptor, version, paths | tau≥0; FIFO and boundary tests | Derived from network/profiles; no undocumented supplied matrix |
| `missing_forecast_policy`, `closure_policy` | Enums | data contract | reject; support alternatives only with tests |
| `distance_policy`, `benchmark_references` | Metric/rounding and cost/status/source records | manifest | Required for gap; unknown reference gives null gap |

| Search/experiment field | Type; units/range | Source and default policy; validation (all planned) |
|---|---|---|
| `runtime_budget`, `iteration_budget` | positive seconds/integer iterations | Run config, mandatory at least one; log both and stop reason |
| `random_seeds`, `repetition_count` | integer list, positive count | Frozen experiment config; matching lengths |
| `traffic_scenario_selection` | list of valid IDs | Manifest; explicit development/final split |
| `neighborhood_settings` | supported operator names, candidate count 1…n−1 when n>1 | Development config; singleton special case, reject unimplemented operators |
| `feasibility_repair_settings` | methods and finite nonnegative attempt/time limits | Development config; explicit failure after exhaustion |
| `penalty_parameters` | nonnegative capacity/time penalties in objective-compatible units | Only for selected infeasible search mode; final feasibility always hard |
| `discretization_resolution` | positive Delta minutes | Exact-test config; sensitivity runs, no universal resolution |
| `caching_settings` | byte limit ≥0, key/precision policy | Profiled config; zero disables cache; scenario/version invalidation |
| `performance_settings` | workers≥1, propagation policy, optional compiled backend | Measured config; serial reference first, resource accounting |
| `schedule_optimization_budget` | nonnegative seconds and tolerance minutes | Development config; no route marked optimal from earliest schedule alone |
| `benchmark_manifest`, `reference_tolerance` | paths and nonnegative numeric tolerances in declared units | Frozen protocol; positive reference before percentage gap |

Data schemas should include checksum, source IDs, dimensional units and input validity diagnostics. Wall-clock timestamps for logs are UTC with presentation zone recorded; local delivery windows are converted once at import. Calendar dates and elapsed durations are different types. No changing core equations to adjust n, K, Q, windows or forecast intervals.

## A6. Experiments and figures

Proposed final manifest: **at least 20 distinct instances**, with 8 classical CVRP, 6 CVRPTW and 6 distinct TD-CVRPTW base instances. Confirm this distribution with the tutor; the earlier conservative ambition of 20 published CVRP references remains an optional expanded campaign if resources permit. The official minimum is 20 total, not a documented requirement for 20 per category. Repeated seeds and multiple traffic profiles on the same base do not inflate the headline distinct count. Separate 6–10 development instances across layers; no overlap with final base geometries or derived scenarios.

Category A uses VRPLIB, distance objective, per-family rounding, reference fleet and source-ID audits. Category B should investigate Solomon and Gehring–Homberger sources; no files are bundled. SINTEF's Solomon tables use lexicographic fleet then distance with their stated precision: these are not elapsed-time optima. Run that exact objective convention for a valid published comparison, or report elapsed time without a published gap. Category C needs sourced traffic-aware instances or explicitly synthetic speed scenarios; no certified advanced optimum or real traffic feed is currently established. Keep scenario hashes, windows, service, fleet, horizon, holding/departure rules, objective and precision identical across compared methods.

Use tiny cases (n≤8 when tractable) for enumeration/exact grid checks, medium cases for operators, larger 100/500/1000 cases for scaling and 2000+ synthetic stress tests if feasible. Vary geographic clustering, demand/capacity pressure, narrow/wide windows and synthetic morning/evening/directional peaks. Generate feasible examples from disclosed witness schedules when needed, but hide witnesses from optimization; separately include deliberate infeasible cases. Changing traffic or windows creates a different comparison problem; do not reuse original BKS.

Before final runs, freeze budgets, versions, hardware, seeds (propose five, adjust by declared compute budget), preprocessing inclusion, failure/timeout policy and manifests. Report feasibility over all attempts; quality statistics among feasible runs with explicit denominators. Report best/mean/median/std/worst, paired instance differences, bootstrap intervals where meaningful and outliers. Never pool minutes, distance gaps and hierarchical fleet scores into a single mean. Baseline improvement is 100(C_base−C_ours)/C_base for positive comparable baseline cost; it is not a certified optimality gap. Reference gap remains 100(C_ours−C_ref)/C_ref only for C_ref>0 and an identical problem; otherwise null.

Save routes and schedules, path traces, forecast/source hashes, policy/units, initial/final/best objective, distance, driving/waiting/service, departure/return, makespan, fleet, maximum lateness, status, time-to-first-feasible, runtime/preprocessing, peak RSS, seed, commit and config hash. Replaying planned routes under perturbed forecasts measures robustness, not observed actual traffic performance. Label observed arrivals only when measurements exist.

| Planned figure | Scientific question |
|---|---|
| Customer map with windows; routes colored by truck | How do geography and temporal compatibility shape assignment? |
| Segment congestion heatmap and daily profiles | When and where do forecasts alter travel? |
| Planned vs replayed arrivals; window bands | Which forecast errors threaten feasible service? |
| Waiting bars and vehicle Gantt timelines | Is elapsed time dominated by driving, service or waiting? |
| Service-start slack/violation plot | Are hard windows respected, including boundary cases? |
| Objective convergence and paired quality comparisons | Which method improves quality within matched budgets? |
| Runtime and peak RAM versus n and time resolution | Which representation or evaluator becomes limiting? |
| Traffic intensity/window tightness sensitivity | Where does reliability degrade? |
| Distance-optimal versus time-aware route/path maps | How much distance is exchanged for elapsed-time improvement? |
| Failure/timeout counts and seed distributions | Are apparent gains robust across all attempted runs? |

## A7. Engineering and validation

Compare ALNS with time-aware related removal/regret repair and ILS with feasible perturbation/local search on the same development data, evaluator and wall-time budget. Tabu search and hybrid methods are credible research candidates, not predetermined winners. Investigate relocate, swap, Or-opt, 2-opt, 2-opt*, cross-exchange and SWAP* adaptation; every reversal and tail exchange must propagate schedules. Savings is a Layer 1 baseline; advanced constructors use capacity- and time-feasible insertion. Keep versioned external comparisons only where the exact supported constraints/objective match. HGS-CVRP is a classical CVRP baseline; PyVRP's time windows and routing profiles do not establish departure-time-dependent traffic support. No external TD baseline is confirmed by this task.

For any changed route, recompute from the earliest affected predecessor through the suffix, including changed road paths, interval crossings, waiting, service windows and depot return. A static distance delta cannot evaluate Layer 3. Reuse a suffix only when the full downstream state (time, load, policy and forecast/path version) provably agrees; early termination based solely on a small objective difference is unsafe. A flexible-departure schedule may require reoptimizing the whole route.

Independent validator contract: consume immutable instance, routes, departure choices and any deliberate holding; check IDs, each customer exactly once, no splits, fleet rule, connectivity, capacities, reachable road paths, forecast coverage, continuous traversal, all arrival/start/completion/departure/wait times, window policy and return limits. Recompute objective and distance from physical paths independently of search caches. Return feasible flag, structured reasons, per-stop schedule/slack, route loads and all metrics. Unused trucks contribute zero schedule and objective. Invalid/timeout/no-feasible-found/proven-infeasible are distinct outcomes. Best-feasible storage must not alias mutable search state; final outputs always pass a full audit.

Future tests: early waiting, exact opening/closing, completion versus start policy, service-induced late suffix, departure at/near forecast boundaries, multi-period traversal, FIFO order tests, asymmetry, path switches, unreachable roads, horizon overrun, missing forecast, invalid units/DST, inactive trucks, zero demand/service/travel, duplicates, non-first depot, bin-packing counterexample and full-capacity trucks. Check incremental versus independent propagation for randomized moves, inverse moves and label permutations. With broad windows, zero service and constant tau proportional to d, validate Layer 1-compatible schedules under a sufficient horizon and fixed departures. For arbitrary restrictive windows or flexible departure conventions, do not claim an automatic objective equivalence.

Performance plan: dense static matrix is about 8(n+1)² bytes; a dense h-slice temporal table multiplies that by h. Prefer road-profile storage, on-demand paths, bounded exact caches, candidate neighbor lists, prefix schedule state and selective route evaluation. Naive regret insertion can examine O(n²) positions each with O(n) propagation plus path costs; measure these costs. Profile CPU/RSS, path-oracle calls and cache accuracy before compilation or decomposition. Candidate restrictions need occasional wider search and quality ablations. No thousands-customer speed or quality guarantee follows from this design.

## A8. Status, decisions and next steps

Inspection at starting commit `da20370` on `main` found README.md, context.md, sources.md, CVRP_Implementation_Plan_Audit.md, CesiCDP_CVRP_Modeling.ipynb and the unrelated animation guide. The repository exists at [DennixAI/EcoRoute-CVRP](https://github.com/DennixAI/EcoRoute-CVRP). The only notebook has 68 cells (39 Markdown, 29 code), 19 saved PNG outputs and no saved error outputs. Its full cell source was inspected; it has static CVRP generation, parsing, supplied-route checking and equation certification. Saved outputs are not a fresh execution or tutor approval.

`CesiCDP_CVRP_Detailed_Modeling.ipynb`, `CesiCDP_CVRP_Mathematical_Modeling.ipynb`, the package ZIP, standalone benchmark files and short README named in earlier history are **not present**. Do not assume file equivalence merely from counts. The current notebook embeds A-n32-k5 text, but its fleet parser infers -k as an upper limit and its `original_ids` stores parser indices; both need explicit correction/verification in the next notebook phase. Its generic rounding path also needs format-specific guarding. The notebook is intentionally unchanged in this documentation task.

| Stage | Evidence now | Required next evidence |
|---|---|---|
| Documentation upgrade | This reviewed specification and synchronized roadmap | PR review; not tutor approval |
| Modeling notebook | Classical draft exists, saved outputs | Layer 2/3 equations, tests, clean run and tutor feedback |
| Optimization | No constructor, main search or exact solver | Canonical schema, validator, prototypes, selected own algorithm |
| Validation | One supplied reference-route demonstration | Frozen manifests, ≥20 distinct instances, raw runs and statistics |
| Final delivery | Planned | Reproducible notebook, English presentation/live demo and confirmed dates |

Open decisions: start versus completion windows; whether pre-service holding and flexible departures match the assignment; total elapsed versus alternative time objectives; exactly/at-most K; depot bounds and fleet-specific schedules; forecast provider/license/resolution and data coverage; time-grid resolution/error tolerance; acceptable public advanced benchmark protocols; tutor approval of external/compiled code; budgets/hardware/seeds; team ownership and absolute deadlines. These are implementation/review gates, not reasons to misstate the now-explicit user-selected advanced scope.

Next sequence: (1) tutor review of this mathematical contract; (2) update the actual notebook in a separate authorized phase with temporal examples and traffic evaluation; (3) implement canonical data/forecast schemas and independent evaluator; (4) validate tiny continuous/discrete cases and baseline reduction; (5) implement feasible constructors and move propagation; (6) run ALNS/ILS comparative development pilots before selecting the main search; (7) profile and accelerate without feasibility loss; (8) freeze and run the stratified final campaign; (9) integrate results, limitations, reproducibility and English defense. All implementation and experiment steps remain pending.

Latest scope-change record: **2026-11-07, explicit user request** selected Layer 3, retained Layers 1/2, required documentation-only changes and a review PR rather than a direct main push. Earlier prompts below are preserved verbatim as history. Further research and official links are in [sources.md](sources.md); the [README](README.md) gives execution gates and the [audit](CVRP_Implementation_Plan_Audit.md) reassesses risks.

---

> **Purpose:** long-form context handoff for the GitHub repository `EcoRoute-CVRP`. This file is designed so that a future teammate, contributor, or AI assistant can resume the project without relying on conversational memory.
>
> **Language policy:** communicate, document, and explain in **English**. The **original French assignment is preserved in [`sources.md`](sources.md)**; it must not be silently translated or altered.
>
> **Context snapshot:** 2026-11-07. This document summarizes the original assignment provided in the conversation and consolidates project decisions, technical modeling, deliverables, user requirements, and the planned development roadmap. The original source and references are in `sources.md`.
>
> **Source precedence:** (1) original assignment; (2) explicit, later user decisions for the chosen implementation; (3) actual repository implementation evidence; (4) recorded tutor feedback; (5) prior assistant recommendations, which are not binding decisions. Any contradiction must be recorded, not concealed.

## Contents

1. [Complete inventory of known project context](#1-complete-inventory-of-known-project-context)
2. [Project identity and executive context](#2-project-identity-and-executive-context)
3. [Original French assignment](#3-original-french-assignment)
4. [Official requirements extracted from the assignment](#4-official-requirements-extracted-from-the-assignment)
5. [Confirmed decisions vs proposals vs unresolved questions](#5-confirmed-decisions-vs-proposals-vs-unresolved-questions)
6. [CVRP modeling: sets, parameters, objective and full ILP](#6-cvrp-modeling-sets-parameters-objective-and-full-ilp)
7. [Parameterization contract: no hard-coded instance values](#7-parameterization-contract-no-hard-coded-instance-values)
8. [Synthetic inputs, VRPLIB and benchmarking conventions](#8-synthetic-inputs-vrplib-and-benchmarking-conventions)
9. [What has been implemented and what has not](#9-what-has-been-implemented-and-what-has-not)
10. [Detailed end-to-end project roadmap](#10-detailed-end-to-end-project-roadmap)
11. [Performance evaluation and statistical protocol](#11-performance-evaluation-and-statistical-protocol)
12. [Architecture, reproducibility, testing and team work](#12-architecture-reproducibility-testing-and-team-work)
13. [Sources and references](#13-sources-and-references)
14. [Chronological user prompts and explicit instructions](#14-chronological-user-prompts-and-explicit-instructions)
15. [Assistant decisions, suggested approach and corrections](#15-assistant-decisions-suggested-approach-and-corrections)
16. [Open questions, risks, limitations and next action](#16-open-questions-risks-limitations-and-next-action)
17. [Project artifacts and current deliverable status](#17-project-artifacts-and-current-deliverable-status)
18. [Tutor defense preparation checklist](#18-tutor-defense-preparation-checklist)

---

## 1. Complete inventory of known project context

This is an inventory; the following sections contain the full details. **User requirements** and **suggestions** are distinguished throughout. The related project-history excerpt also contains earlier user instructions emphasizing algorithm quality and exhaustive review; those are transcribed in Section 14.

- **Identity:** `EcoRoute-CVRP`; descriptive name “EcoRoute — Intelligent Delivery Route Optimization”; CesiCDP; ADEME project; CESI Algorithmics and Optimization 2026–27; four-person team; environmental mobility and urban logistics context.
- **Original material:** long French environmental/assignment introduction; original basic and advanced problem descriptions; organization; first-check modeling rules; final deliverable; oral defense; evaluation criteria; both CESI links and the GitHub VRPLIB link supplied by the user.
- **Original broader domain:** minimize delivery tour duration on a road network taking time-varying traffic into account; this is broader than a static CVRP. The first notebook used CVRP with distance; the latest user decision selects TD-CVRPTW and a time-based objective (A1–A4).
- **Chosen problem:** **TD-CVRPTW**, retaining classical CVRP as Layer 1 and CVRPTW as Layer 2. All customers serviced exactly once by a fleet of identical-capacity trucks, starting and ending at one depot, with payload limitations and no disconnected tours.
- **Math:** sets $V,C,F,A$; data $n,K,Q,q_i,d_{ij}$; arc variables $x_{ijk}$; assignment variables $y_{ik}$; active-truck variables $z_k$; order variables $u_{ik}$; minimize total distance; coverage, flow, depot, capacity, MTZ, domain and self-loop rules; optional symmetry breaking; TSP reduction; decision NP-completeness vs optimization NP-hardness; model sufficiency/necessity.
- **Configurable inputs:** customer count, depot/index mapping, fleet upper bound, shared vehicle capacity, per-customer demand, coordinates, graph, distances and rounding, synthetic generation distribution, seeds, benchmark paths/fleet override, and future solver, experiment and plot parameters. *Rules remain fixed even when data vary.*
- **Data:** synthetic examples plus actual VRPLIB benchmarks; `vrplib` library; `A-n32-k5` illustrative instance (31 customers + 1 depot, published **minimum number of vehicles** 5, capacity 100, proven optimum 784); avoid comparing unrounded costs with rounded reference costs; preserve original source IDs.
- **First notebook:** previous assistant reported an executable 68-cell notebook (39 Markdown, 29 Python code), 19 plotted figures, detailed equations, proof, synthetic generator, sample data, reference-route validation, explicit constraint-equation certification, sensitivity analysis; **no optimization solver**. Tutor approval has **not** been reported.
- **User-specified presentation:** extensive plots, high-detail code comments, extensive story-driven English explanations, notebook format `.ipynb`, academic literature, source links, clear assumptions, parameterized rather than hard-coded modeling.
- **Later code:** build and test initial solution construction, local search, and a metaheuristic, **with ALNS only a recommended candidate**, not yet committed or implemented; scale to realistic hundreds/thousands of customers; optimize code performance; **critically compare multiple competitive algorithms/baselines rather than assuming the first approach is good** (explicit user priority).
- **Experiments:** minimum 20 *different* instances across scenarios; compare to optimal/BKS where available; cost, runtime, feasibility, gap, statistical robustness, standard deviations, sensitivity to capacity/size/distribution/parameters, limitations and interpretations; warning that gaps above roughly 7–10% cap grade at B as stated by the assignment.
- **Deliverables:** mathematical modeling, algorithm design and implementation, experimental study, presentation in English, consolidated final notebook; first check during Prosit 3, final notebook before defense, presentation on final day of block; ADEME “July 12 next” in undated original brief (year not unambiguously stated).
- **Team/repository:** four-member division of responsibility was proposed; `EcoRoute-CVRP` was **suggested by the assistant after the user requested a GitHub-suitable name**, and was explicitly accepted and created by the user-directed repository setup. The remote is https://github.com/DennixAI/EcoRoute-CVRP. The list of deliverables and their implementation status is recorded below.
- **History:** earlier project conversation excerpts (quality and exhaustive-review requirements), original French brief; subsequent English-only instruction; questions about ILP meaning; model + Python request; full checklist and configurability request; request for a large illustrated notebook and clarification; final detailed notebook specification; progress explanations; repository name selection; current context compilation request. Exact wording is retained in Section 14.
- **Unknowns:** exactly $K$ versus at most $K$ active vehicles, tutor approval, the advanced time objective and window/holding policies, final benchmark inventory, exact defense dates, final ALNS/other algorithm choice, software runtime limits and hardware, benchmark fleet metadata for all data, dataset usage conditions and actual traffic sources.

---

## 2. Project identity and executive context

| Item | Recorded value / state | Authority |
|---|---|---|
| Repository name | **`EcoRoute-CVRP`**, existing repository | Verified repository and user-directed creation/push history |
| Project title | **EcoRoute — Intelligent Delivery Route Optimization** | Assistant-proposed title |
| Short technical subtitle | Mathematical Modeling and Optimization of the Capacitated Vehicle Routing Problem (CVRP) | Assistant-proposed subtitle |
| Original organization | **CesiCDP** | French brief |
| Funding/stakeholder context | **ADEME**, interest in mobility demonstrators and new solutions | French brief |
| Academic setting | CESI / A3 Algorithmique et optimisation 2026–27 URL path | Provided assignment URL; cohort context implied by path |
| Team size | **4 people** | French brief |
| Intended application | Optimizing delivery vehicle routes | French brief + confirmed user choice |
| Original task objective | **Minimize total travel duration**, considering predicted traffic in different time slots | French brief |
| Current proposed mathematical objective | Minimize total elapsed route time; distance remains Layer 1 objective | Latest user scope, A2; tutor interpretation pending |
| Main problem | **TD-CVRPTW**, Layer 3 | Latest explicit user decision; see A1 |
| Advanced alternative | CVRPTW with time windows and waiting, Level A | Official Level A and now an included layer of the selected target |
| Requested implementation language | Python | Brief + user |
| Delivery formats | Jupyter notebooks with explanation and code; final oral defense in English | Brief + user |
| First-modeling stage solver | **Not required and explicitly not to be implemented** | Brief + user |
| Final solver implementation | **Required** with metaheuristic and real-size tests | Brief |
| Proposed metaheuristic | ALNS, with other choices eligible | Prior assistant recommendation; **not a final user decision** |
| Current recorded state | Modeling notebook draft reported completed and executed; **awaits tutor review** | Modeling deliverable status from previous project work |
| Repository creation | Established | https://github.com/DennixAI/EcoRoute-CVRP |

### Environmental and business motivation

Since the 1990s, international and national action to reduce energy consumption and greenhouse gas emissions has highlighted transport as a high-impact sector. The original brief cites the 1997 Kyoto Protocol (in force in 2005), later emission reduction commitments, and the need for public authorities to influence behavior. CesiCDP is positioned as a mobility-research organization responding to an ADEME interest call; improving the efficiency of logistics is the project's demonstration use case. Potential relevant fields mentioned: postal distribution, product delivery, road network maintenance/treatment, waste collection.

### Scope distinction (critical for future AI assistants)

The latest user request explicitly upgrades the final target to TD-CVRPTW. Classical distance CVRP remains the foundational baseline and the existing notebook scope. Follow A1–A8 for advanced modeling, objectives, parameters, benchmarks and release gates. Historical CVRP-only prompts in Section 14 describe the earlier checkpoint.

---

## 3. Original French assignment

The source text and normalization notes are preserved in [`sources.md`](sources.md#1-original-french-assignment-as-provided-in-the-conversation). Section 4 summarizes the requirements relevant to this project.

---

## 4. Official requirements extracted from the assignment

### 4.1 Basic version

- Choose a mathematical model and implement **Python code** able to handle substantial instances (the brief mentions *several thousand cities* as ambition).
- Perform a **statistical study of the algorithm's experimental behavior**.
- Use a fleet of $k$ trucks with **identical capacity**.
- Resolve a vehicle-routing optimization problem using Operations Research methods.

### 4.2 Advanced version — included in the latest selected target

- Delivery windows per object/customer.
- No service outside time window.
- Waiting allowed until time window opens.
- Named problem in evaluation section: **CVRPTW** (Level A), versus basic **CVRP** (Level B).
- Time-dependent predicted traffic is also mentioned in the wider introduction, but the brief's Level B/Level A distinction explicitly names CVRP/CVRPTW.

### 4.3 Project stages and checkpoints

1. **Formal mathematical modeling:** Jupyter notebook that introduces context and formalizes data/problem/objective; theoretical complexity; preliminary PLNE variables, objective, complete relevant constraints; no solving method and no solver implementation at this check. Review with tutor (formalization relevance, complexity proof, model coherence). Deadline: during **Prosit 3**; check not graded according to supplied text.
2. **Algorithm design and implementation:** choose an appropriate heuristic/metaheuristic; define solution representation, neighborhoods, operators, adaptive/guidance mechanism, initialization, iteration, stopping, and Python execution.
3. **Experimental study:** structured scenarios, tables, metrics, comparison, quality, runtime, robustness, sensitivity, statistical arguments, limitations and improvements.
4. **English team presentation:** professional explanation of context, objectives, progress and results, with a short live code demonstration and an honest schedule of completed/in-progress/remaining work.

Each stage yields a deliverable in **notebook** form showing reasoning and code where implementation is expected; prioritize **storytelling**. Code need not be industrial production code but should be readable, commented, reasonably performant, and follow PEP guidance.

### 4.4 Final deliverable

- **Due:** day before the defense.
- Include corrected full PLNE, proof of complexity, model data, possible use of exact ILP approach (direct solve, benchmark, bounds, or note if unused).
- Explain and formalize chosen metaheuristic and implement it in Python, with test cases and demonstrations.
- Test on **at least 20 distinct instances** across scenarios; not merely 20 random seeds of the same instance.
- Measure quality and execution time as a function of instance size, including feasibility and sensitivity.
- Use **`vrplib`** to load reference instances, compare with known solutions and compute gaps.
- Oral defense on last day of block; results-oriented, English, sufficiently small live demo; plan/schedule appreciated.

### 4.5 Gap formula and interpretation

Original formula in the brief:

$$\text{gap}(\%)=100\cdot\frac{\text{our cost}-\text{optimal cost}}{\text{optimal cost}}.$$

**Rigorous correction of terminology:** if the denominator is a *proven optimal cost*, this is an optimality gap. If the denominator is merely a **Best-Known Solution (BKS)**, call it “gap to BKS.” A solution can be equal to or better than a previously published BKS; therefore BKS gaps are **not the same** as mathematically certified optimality gaps. Reference costs, distance rounding, and feasibility conventions must align.

### 4.6 Evaluation emphases

- Solution quality, especially gap (brief warns that gap > about **7–10%** limits maximum grade to B).
- Computation time.
- Quality of experimental analysis, interpretation, and justified conclusions.
- Acknowledge strengths, weaknesses, and improvements.

---

## 5. Confirmed decisions vs proposals vs unresolved questions

| Topic | Status | Explanation |
|---|---|---|
| Language | **Explicitly confirmed** | User requested **English only** for responses/documentation (original assignment reproduced in French as evidence). |
| Current target | **Explicitly confirmed, 2026-11-07** | TD-CVRPTW; notebook still implements Layer 1 modeling only. |
| Main objective | **Advanced proposal** | Total elapsed route time (A2); distance remains the historical Layer 1 benchmark objective. |
| Data selection | **Explicitly confirmed** | Both generated synthetic examples **and** VRPLIB benchmark instances. |
| Modeling code scope | **Explicitly confirmed** | Plotting, parsing, constraint illustrations, **feasibility checks**, **no optimization solver**. |
| Modeling deliverable | **Explicitly confirmed** | Detailed `.ipynb`, rigorous ILP/PLNE, all necessary constraints, MTZ, complexity proof, numerous plots, detailed comments, references, downloadable file. |
| Configurability | **Explicitly confirmed** | **No fixed instance values** baked into the mathematics or future algorithm; capacity/fleet/demand/locations/costs adjustable. |
| Project repository | **Verified** | https://github.com/DennixAI/EcoRoute-CVRP exists and has main. |
| Vehicle fleet semantics | **Open** | At most $K$ vs exactly $K$ active; existing model uses **at most $K$**. Tutor to validate. |
| Fleet capacities | **Confirmed by brief** | Identical capacities across all trucks within an instance, but $Q$ varies between instances. |
| One depot, visit exactly once, no split | **Model assumption consistent with standard CVRP** | Should still be confirmed with provided problem instance conventions. |
| Zero customer demand | **Model supports it** | Order-based MTZ works even for zero-demand customers. |
| Symmetric Euclidean graph | **Not a universal assumption** | General directed nonnegative cost matrix supported; plots may use Euclidean coordinates. |
| Time-dependent traffic | **Included in target; not implemented** | Integrated forecast evaluation specified in A3. |
| Initial route constructor | **Candidate only** | Greedy insertion / Clarke–Wright Savings previously proposed. |
| Local search | **Candidate only** | 2-opt, relocate, swap, 2-opt*. |
| Metaheuristic | **Recommended, not finalized** | **ALNS** suggested. No algorithm implementation or benchmark performance established. |
| Final benchmarks | **Not selected** | Need minimum 20 diverse instances; one sample A-n32-k5 previously validated. |
| Hardware/time budgets | **Not set** | Needed for experimental fairness, reproducibility and scalability. |
| Tutor approval | **Not established** | Modeling draft reported completed; checkpoint approval still pending. |
| Year of “July 12” | **Unclear** | Do not assume a particular year without confirming current academic scheduling. |

---

## 6. CVRP modeling: sets, parameters, objective and full ILP

### 6.1 General graph and input data

- $C=\{1,2,\dots,n\}$ customers; $0$ depot; $V=C\cup\{0\}$.
- $F=\{1,\dots,K\}$ identical-capacity available trucks.
- $A=\{(i,j):i,j\in V,\ i\ne j\}$ potential directed arcs; complete graph for main ILP, possibly built from shortest paths on the road network.
- $q_i\ge0$ customer demand and $q_0=0$.
- $Q>0$ common truck capacity, **input** not a fixed universal number.
- $d_{ij}\ge0$ fixed distance/cost of driving from $i$ to $j$, **input**. Symmetry is not required.
- Optional $(X_i,Y_i)$ customer/depot coordinates, for maps and possibly constructing Euclidean distances; cost matrix remains authoritative.
- $n,K,Q,q_i,d_{ij}$ are **instance parameters**; the ILP equations are unchanged across instances.

### 6.2 Decision variables

$$x_{ijk}\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ uses arc } (i,j).$$
$$y_{ik}\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ serves customer } i.$$
$$z_k\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ is active}.$$
$$u_{ik}\ge0:\quad \text{auxiliary relative visit order for customer } i \text{ on truck } k.$$

**Classification note:** If $u_{ik}$ is continuous, technically this is a **Mixed-Integer Linear Program (MILP)**; setting $u_{ik}\in\mathbb{Z}_{\ge0}$ instead yields an **all-integer PLNE** with the same interpretation. The original conversation used both descriptions; a final report should consistently define its domain.

### 6.3 Layer 1 objective

**Minimize total traveled distance over all trucks and selected arcs:**

$$\boxed{\min\sum_{k\in F}\sum_{(i,j)\in A}d_{ij}x_{ijk}}.$$

The later empirical comparison must use **the exact benchmark cost convention**. This objective defines Layer 1. The active advanced objective and temporal extension are in A2–A4.

### 6.4 Complete constraints (at most $K$ active trucks)

**Customer assignment (every customer exactly once):**

$$\boxed{\sum_{k\in F}y_{ik}=1\qquad\forall i\in C.} \tag{M1}$$

**Every assigned truck leaves its customer exactly once:**

$$\boxed{\sum_{j\in V\setminus\{i\}}x_{ijk}=y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M2}$$

**Every assigned truck enters its customer exactly once:**

$$\boxed{\sum_{j\in V\setminus\{i\}}x_{jik}=y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M3}$$

**Each active vehicle leaves depot once:**

$$\boxed{\sum_{j\in C}x_{0jk}=z_k\qquad\forall k\in F.}\tag{M4}$$

**Each active vehicle returns to depot once:**

$$\boxed{\sum_{i\in C}x_{i0k}=z_k\qquad\forall k\in F.}\tag{M5}$$

**Per-vehicle carrying capacity:**

$$\boxed{\sum_{i\in C}q_i y_{ik}\le Q z_k\qquad\forall k\in F.}\tag{M6}$$

**Auxiliary ordering variable bounds:**

$$\boxed{y_{ik}\le u_{ik}\le n y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M7}$$

**MTZ subtour elimination (valid with zero-demand customers):**

$$\boxed{u_{jk}\ge u_{ik}+1-(n+1)(1-x_{ijk})\qquad\forall i,j\in C,\ i\ne j,\ k\in F.}\tag{M8}$$

**Domains:** $x,y,z$ binary; $u\in\mathbb R_{\ge0}$ (or integer nonnegative). No self-loops $x_{iik}$ because $(i,i)\notin A$. 

**Optional symmetry reduction:** $z_k\ge z_{k+1}$ for identical truck indices, if desired; not needed for feasible-model completeness.

### 6.5 Interpretation and validity

- M1 + M2/M3 give one assignment, one arrival and one departure for every customer.
- M4/M5 ensure one depot-out and one depot-in per active truck, zero depot arcs for inactive trucks.
- M6 prevents overloading and links assigned demand to use. With zero-demand customers, M1–M5 and MTZ still enforce the correct route structure.
- M7/M8 exclude disconnected customer-only cycles: traversing each customer-to-customer selected arc must increase order by at least 1; a closed directed customer-only cycle would require a strict increase back to the start, impossible.
- With all core equations, every active truck's selected arcs form **one connected depot tour**. Every physically feasible no-split CVRP tour is expressible by these variables, and every feasible assignment encodes a valid plan.
- If assignment **must use exactly $K$ trucks**, impose $z_k=1$ for all $k$ and check that the instance permits $K$ nonempty tours; this is not currently assumed.
- Other subtour formulations are possible. This specific $n+1$ big-$M$ coefficient is linked to the order bounds ($u\in[0,n]$), not an arbitrary tunable optimization hyperparameter.

### 6.6 Complexity proof

Start with TSP on $n+1$ vertices with distances $d_{ij}$ and budget $B$. In polynomial time, construct CVRP with $0$ as depot, $K=1$, $q_i=1$ for $i\ge1$, and $Q=n$, preserving the original distance matrix. Its single truck can serve all $n$ customers. Feasible CVRP tours are exactly TSP Hamiltonian cycles with the same cost. Thus $\text{TSP}\le_p\text{CVRP}$. The **optimization** CVRP is NP-hard. The **decision** variant (is a feasible set of routes of cost $\le B$ available?) belongs to NP under standard finite integer/rational encoding, because a proposed route list can be verified in polynomial time. The decision problem is therefore NP-complete.

### 6.7 Necessary feasibility diagnostics (not sufficient)

$$\max_{i\in C}q_i\le Q,\qquad\sum_{i\in C}q_i\le KQ.$$

Aggregate lower bound on the number of vehicles: $\lceil\sum_iq_i/Q\rceil$. These conditions are **necessary**, not sufficient for unsplittable demand. Example: demands (6,6,6), $K=2$, $Q=10$. Total demand 18 $\le20$, but each vehicle can hold only one customer, so the instance is infeasible under two trucks.

### 6.8 Mathematical-model scaling

For the complete directed graph with $n$ customers and $K$ trucks:

- Arc binaries: $K(n+1)n$.
- Customer-assignment binaries: $Kn$.
- Vehicle activation binaries: $K$.
- Order auxiliaries: $Kn$.
- MTZ pairwise inequalities: $Kn(n-1)$.
- Total binary variables: $K(n+1)^2$.

Therefore this explicit three-index model has $\Theta(Kn^2)$ arc variables/MTZ inequalities. Mathematical correctness **does not imply** tractability on several-thousand-customer inputs with an exact solver; later heuristic/metaheuristic methods are required for scalability.

---

## 7. Parameterization contract: no hard-coded instance values

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

### 7.1 Principle

**Do not hard-code data values into the model/algorithm.** “$Q$ is shared across trucks” is a model rule; “$Q=100$” is only an input value for a specific benchmark. The final algorithm should accept multiple instance configurations without rewriting code. Hand-written small examples may of course use numerical demonstration values.

### 7.2 Input and configuration parameters

| Group | Parameter | Notation / coding field | Role | Source/status |
|---|---|---|---|---|
| Problem size | Customers | $n$ / `n_customers` | Number of non-depot nodes | From instance / synthetic configuration |
| Fleet | Available trucks | $K$ / `max_vehicles` | Upper bound on active routes | From metadata or explicit override |
| Capacity | Uniform vehicle capacity | $Q$ / `vehicle_capacity` | Limit per truck | Instance |
| Demand | Customer demands | $q_i$ / `demands` | Nonnegative per-customer delivery load | Instance |
| Geography | Depot location | `depot`, `depot_xy` | One configurable depot; internally reindex to 0 | Instance |
| Geography | Customer locations | `coordinates` | Spatial visualization or distance derivation | Instance/optional |
| Network | Allowed arcs | $A$ | Feasible stop-to-stop connections | Complete graph or derived network |
| Costs | Travel-distance matrix | $d_{ij}$ / `distances` | Layer 1 objective costs; secondary advanced distance metrics require selected road paths | Instance |
| Costs | Rounding convention | `distance_policy` | Align VRPLIB costs with BKS | Benchmark-specific |
| IDs | Original node ID mapping | `original_ids` | Translate depot/customer labels to canonical indices | Parsing |
| Synthetic | Layout type | `layout` | Uniform vs clustered generation | Configuration |
| Synthetic | Demand bounds | `min_demand`, `max_demand` | Generated demand range | Configuration |
| Synthetic | Coordinate range | `coordinate_max` | Geometric data range | Configuration |
| Synthetic | RNG seed | `seed` | Repeatable generation | Configuration |
| Benchmark | VRP/SOL paths | `BENCHMARK_PATH`, `.sol` path | Local files | Configuration |
| Benchmark | Fleet override | `BENCHMARK_FLEET_OVERRIDE` | Explicit maximum fleet when omitted in file | Configuration |
| Algorithm (future) | Maximum iterations | `max_iterations` | Stopping budget | Not yet implemented |
| Algorithm (future) | Time limit | `time_limit_seconds` | Runtime budget | Not yet implemented |
| Algorithm (future) | Random state | `random_seed` | Reproducibility | Not yet implemented |
| Algorithm (future) | Candidate neighbors | `candidate_neighbors` | Local-search acceleration | Not yet implemented |
| Algorithm (future) | Removed customer fraction | `destroy_fraction` | ALNS perturbation strength | Candidate only |
| Algorithm (future) | Operator weights | e.g. `operator_weights` | Adaptive destroy/repair choice | Candidate only |
| Algorithm (future) | Acceptance settings | e.g. `initial_temperature`, `cooling_rate` | Simulated-annealing-type acceptance if chosen | Candidate only |
| Algorithm (future) | No-improvement patience | e.g. `max_stagnation` | Search stopping/restart | Candidate only |
| Experiments | Number of instances | $N_{\text{instances}}\ge20$ | Distinct dataset requirement | Required later |
| Experiments | Repeated runs | $R$ / `n_runs` | Mean, std, robustness | To decide |
| Experiments | Seeds | `run_seeds` | Reproducibility/fairness | To decide |
| Experiments | Hardware and budgets | `cpu`, `ram`, `time_budget` | Fair cross-instance comparisons | To document |
| Plots | Figure options | labels, dimensions, color map | Presentation-only; not optimization | Configurable options |

**Important:** proposed algorithm parameters are planned configuration fields, **not evidence of existing implementation**. Some settings (e.g., ALNS weights and temperature) only apply if the selected search method uses them.

### 7.3 Previously used *demonstration-only* values

The prior notebook-development record shows a synthetic configuration with illustrative defaults:

```python
@dataclass(frozen=True)
class SyntheticConfig:
    n_customers: int = 42
    max_vehicles: int = 8
    vehicle_capacity: float = 35.0
    min_demand: int = 1
    max_demand: int = 9
    coordinate_max: float = 100.0
    depot_xy: tuple[float, float] = (50.0, 50.0)
    layout: str = "uniform"  # or "clustered"
    seed: int = 2026
    distance_policy: str = "raw"  # raw / nearest_integer / ceil
```

A small hand-written teaching example used:

```python
EXAMPLE_COORDS = [
    [50, 50], [14, 70], [21, 42], [35, 16],
    [75, 76], [86, 45], [62, 20],
]
EXAMPLE_DEMANDS = [0, 6, 5, 4, 7, 3, 2]
EXAMPLE_CAPACITY = 16.0
EXAMPLE_MAX_VEHICLES = 3
EXAMPLE_ROUTES = [[1, 2, 3], [4, 5, 6]]  # manually supplied, not optimized
```

These are **examples only**, never universal constants in the math or future solver. The user's explicit requirement was to support arbitrary meaningful capacity, fleet, demand, and customer-count values.

---

## 8. Synthetic inputs, VRPLIB and benchmarking conventions

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

### 8.1 Required data sources

1. **Synthetic CVRP instances:** configurable number of customers; random seeds; uniform or clustered locations; adjustable demand ranges, depot, capacity and fleet count; cost matrix from coordinates or supplied data. Generation does not construct optimal routes.
2. **VRPLIB instances:** use the actual `vrplib` package to read benchmark files; extract capacity, demand, coordinates/edge weights, depot, and available vehicle limit (if provided). Retain source IDs and map depot to internal index 0.
3. **Reference solutions:** parse `.sol` records when available, validate their feasibility, recompute their cost using the correct edge-weight convention and distinguish a published optimum from an unproven best-known cost.

### 8.2 Benchmark example previously used

| Field | Recorded A-n32-k5 value |
|---|---|
| Benchmark family | Augerat Set A, CVRP |
| Name | `A-n32-k5` |
| Nodes | 32 including one depot |
| Customers | 31 |
| Vehicle count | 5 in the reported reference solution. **CVRPLIB labels `K=5` as the minimum number of vehicles, not as the number of available trucks in every model.** |
| Truck capacity | 100 |
| Edge representation | `EUC_2D` coordinates, rounded to nearest integer for this reference |
| Reference cost | 784, marked **proven optimal** in the CVRPLIB catalog for A-n32-k5 |
| Reference routes | Five benchmark reference tours used as **validation input**, not optimized by the notebook |
| Prior validation | Published cost recomputed as 784; route feasibility and ILP equations reported as passed |

**Historical reference route sequences (internal IDs):**

```text
Route #1: 21 31 19 17 13 7 26
Route #2: 12 1 16 30
Route #3: 27 24
Route #4: 29 18 8 9 22 15 10 25 5 20
Route #5: 14 28 11 4 23 3 2 6
Cost: 784
```

**Do not infer that `-k5` is automatically an upper bound on available trucks.** The dataset and catalog describe 5 as the *minimum number of vehicles*. The current ILP uses an *at-most-$K$* parameter, which must be chosen consistently with the comparison protocol. For this instance, a feasible five-route reference is reported and its cost matches the cataloged optimum. For other instances, confirm the admissible fleet definition before comparing gaps.

The prior notebook contained an embedded text version of `A-n32-k5.vrp` and `.sol` to work offline; the notebook is present as `CesiCDP_CVRP_Modeling.ipynb`, with embedded sample text; standalone sample files are absent (see artifact manifest). The route sequence and cost above reflect the prior recorded notebook and should be revalidated against the authoritative benchmark if reused.

### 8.3 Distance conventions

For coordinates $p_i=(X_i,Y_i)$, raw Euclidean distance is

$$D_{ij}=\sqrt{(X_i-X_j)^2+(Y_i-Y_j)^2}.$$

The recorded Set A reference used **nearest-integer** distances, as modeled by `floor(D + 0.5)` for nonnegative $D$. The `vrplib` documentation confirms that `EUC_2D` is parsed as **unrounded double-precision Euclidean distances**, so users must explicitly apply the benchmark-family convention where appropriate. Do **not** default to NumPy `round` for all instances (ties-to-even behavior). **Do not apply the same rounding rule to every VRPLIB family without checking it.** Preserve `EXPLICIT` edge weights and distinguish `EUC_2D`, `FLOOR_2D`, `CEIL_2D` and `EXACT_2D` rather than blindly applying a generic rule. Published reference cost must be evaluated with the same conventions as produced solutions, or gaps are meaningless.

### 8.4 Fleet metadata caveat

Not all benchmark files include an explicit **maximum available fleet**. `A-n32-k5` has the $k5$ naming convention and a file comment stating **“Min no of trucks: 5”**; the CVRPLIB catalog likewise identifies **minimum number of vehicles = 5**. This is **not automatically** the same concept as an available-fleet upper bound $K$ in our ILP. For a given instance, determine and document whether the benchmark defines a fleet limit, fixes the number of tours, or merely reports a minimum/known route count. If an upper bound is required but absent, obtain the evaluation convention or set an **explicit, disclosed** override.

Do **not** silently translate arbitrary filename suffixes into universally enforced maximum fleet constraints. Comparing a five-vehicle-restricted solution with an unrestricted reference value can be invalid if route-count constraints differ.

### 8.5 Input validation and solution validation

**Data:** ensure valid depot, matching demand lengths and matrix dimensions, nonnegative finite distances and demands, positive vehicle capacity, valid available fleet, consistent coordinates and source IDs, and $q_i\le Q$.

**Candidate routes:** require valid customer labels, exactly one visit each, no duplicate or skipped customers, capacity per route, active routes $\le K$, start/end at depot, and correct distance recomputation. An independent checker can reconstruct the $x,y,z,u$ variables and evaluate all ILP equations; this still does **not** constitute a route solver.

### 8.6 Synthetic example visualization themes from prior notebook

Customer spatial map with demand-colored or demand-sized points; histograms of demands; capacity lines; aggregate feasibility counterexamples; arc-decision diagrams; distance heatmaps; disconnected subtour visuals; MTZ contradiction diagram; hand-written route maps; vehicle load/slack bars; rejected invalid-route scenarios; zero-demand edge case; reference solution routes; per-route reference costs; rounded/unrounded comparison; $Q$ vs vehicle lower bound; $O(Kn^2)$ variable growth; uniform vs clustered distributions; fleet/capacity condition heatmap.

---

## 9. What has been implemented and what has not

### 9.1 Completed modeling deliverable (current project record)

- Actual filename: `CesiCDP_CVRP_Modeling.ipynb`. Earlier differently named artifacts are absent (A8).
- **Recorded deliverable:** 68 cells total, 39 Markdown cells, 29 Python cells, 19 figures; its original creation run completed successfully.
- Sections reported: context and assumptions; graph/data notation; configurable synthetic generation; input checks; geometry and demand visuals; decision variables; distance objective; full constraints and MTZ subtour elimination; complexity proof; route validation and direct equation certification; VRPLIB loading; A-n32-k5 reference checks; parameter sensitivity; model scaling; edge cases; tutor checklist; bibliography.
- Reported dependencies: `numpy`, `pandas`, `matplotlib`, `vrplib` (optional fallback for the embedded simple EUC_2D case), Python/Jupyter.
- Key modeling Python constructs: `SyntheticConfig`, `CVRPInstance`, `euclidean_cost_matrix`, `generate_synthetic`, `validate_routes`, `certify_model_equations`, `load_cvrp`, `parse_reference_solution`, and plotting utilities. **These constructs belong to the modeling deliverable, not the optimization phase.**
- Prior route checker validated existing user/benchmark candidates; **did not construct or optimize routes**.
- Tutor review remains outstanding.

### 9.2 What is definitely NOT completed in the visible conversation

- No coded route-construction optimization algorithm reported.
- No ALNS or other metaheuristic implementation reported.
- No exact ILP solver execution reported.
- No optimization-produced result for A-n32-k5; its cost is a known *reference*.
- No experimental campaign on **at least 20 different instances** reported.
- No empirical algorithm runtime/scalability measurements reported.
- No comparative result gaps from **our own** solver reported.
- No final consolidated notebook or English slide deck/presentation reported.
- No tutor approval or final ADEME submission reported.
- Repository creation, commits and pushes are verified; advanced implementation and results remain absent.

### 9.3 Meaning of “modeling” in this project

**Modeling** means translating logistics into a mathematical optimization problem: what the input means; what choices may be made; what objective is minimized; what constraints characterize feasible routes; how complexity follows from related NP-hard problems. A modeling notebook may contain plotting, data reading, constraint checkers, and illustrative examples **without containing an optimizer**. Algorithm design, solution search, statistical evaluation and presentation are distinct later deliverables.

---

## 10. Detailed end-to-end project roadmap

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

The project phases below consolidate the prior 30-step to-do list with the formal assignment. A checked box means the **prior notebook contains a draft of that component**, not that it has passed tutor review.

### Phase 1 — Classical CVRP foundation (draft present); advanced modeling next

- [x] **1. Define foundational problem/context:** sustainable delivery logistics; historical CVRP notebook scope; one depot; static distance objective; identical-capacity truck fleet; no split deliveries.
- [x] **2. Define data and sets:** $V,C,A,F,n,K,Q,q_i,d_{ij}$, coordinates and depot mapping; describe domains and assumptions.
- [x] **3. Define decisions:** binary arc $x$, assignment $y$, vehicle-use $z$, auxiliary order $u$.
- [x] **4. Define objective:** total fleet distance, including all departure/return legs.
- [x] **5. Define constraints:** exactly-once service, assignment-flow linkage, depot starts/returns, capacity, vehicle activation, zero self-loops, MTZ disconnected subtour elimination, variable domains.
- [x] **6. Prove NP-hardness:** polynomial-time reduction from TSP; distinction between optimization NP-hard and decision NP-complete.
- [ ] **7. Tutor checkpoint:** review equations and edge cases; confirm at-most-$K$ semantics and distance objective; incorporate tutor feedback into the corrected final PLNE. Tutor sign-off remains pending.

**Milestone:** Mathematical Modeling Notebook, during Prosit 3, ungraded checkpoint per assignment.

### Phase 2 — Python environment and datasets

- [ ] **8. Project setup:** organize `.ipynb`, source scripts, `data/`, benchmark and results directories; install packages; lock or record dependency versions; document Python environment/PEP conventions.
- [ ] **9. Dataset pipeline:** configure/load synthetic and VRPLIB baseline instances, CVRPTW windows/service and Layer 3 road forecasts; preserve source IDs, units, fleet policy, forecast epochs/hashes and compatible references (A5–A6).
- [ ] **10. Input validation:** dimension and data checks, nonnegative values, single depot, known/explicit cost matrix conventions, necessary feasibility conditions, clear rejection messages.

### Phase 3 — Algorithm design and implementation

- [ ] **11. Solution representation:** customer route lists plus depot departures, holding choices, per-stop schedules, physical paths, route load, distance, elapsed objective and independent feasibility diagnostics.
- [ ] **12. Initial construction:** compare capacity/time-feasible insertion and regret repair; keep Savings as a Layer 1 candidate; generate independently feasible schedules or report failure.
- [ ] **13. Local search:** 2-opt, relocate, swap, Or-opt, 2-opt* and stronger candidates; propagate affected schedules/paths and audit capacity/windows/return after each accepted move.
- [ ] **14. Metaheuristic:** choose/justify ALNS or another eligible approach; define destroy and repair operators, adaptive selection, acceptance of improving/worsening moves, best-feasible tracking, stopping criteria.
- [ ] **15. Performance/scaling:** exact incremental schedule propagation, path/time caches, candidate lists, profiling, memory analysis, robust stopping and thousands-of-customer trials when feasible.
- [ ] **16. Unit/integration testing:** coverage, capacity, depot, no duplicates, exactly-once, cost calculation, deterministic seeds, edge cases and per-operator validity.

**Milestone:** a layered TD-CVRPTW solver; schedule construction, traffic and cascading move evaluation in A7 are mandatory.

### Phase 4 — Experimental design

- [ ] **17. Curate ≥20 distinct benchmark instances** with varied size, customer distributions, capacity pressure and fleet constraints; use reference costs where available; include synthetic scenarios as warranted.
- [ ] **18. Define protocol:** repeated seeds, uniform hardware/software, runtime or iteration budgets, results schema, parameter tuning split and comparison fairness.
- [ ] **19. Select comparisons:** initial baseline vs metaheuristic; optimal/BKS; optional exact ILP on small cases for proof/bounds; record why each comparison is valid.

### Phase 5 — Benchmark execution, visualization and analysis

- [ ] **20. Execute tests** on ≥20 different instances (with repeated runs of stochastic methods), persist routes and metadata, and track any failures or infeasibility.
- [ ] **21. Assess quality:** cost, feasibility, gap-to-optimum or gap-to-BKS, runtime and difficulty by category; use benchmark-specific distance convention.
- [ ] **22. Analyze statistically:** mean, std, min, max, quartiles, success/feasibility rate, variability between seeds, costs/timing vs size, trends vs capacity/demand/spatial structure, parameter sensitivity.
- [ ] **23. Interpret findings:** explain strengths, weaknesses, difficult scenarios, quality-time trade-offs, scalability, experimental caveats and justified modifications.

**Milestone:** documented experimental-analysis notebook with meaningful data, figures and conclusions.

### Phase 6 — Consolidated final notebook

- [ ] **24. Include corrected formal model** and tutor feedback; explicitly document any use or non-use of an exact solver and valid bounds if applicable.
- [ ] **25. Document chosen algorithm:** solution definition, initialization, operators, neighborhoods, guiding mechanism, iteration, stopping, adjustable settings and technical rationale.
- [ ] **26. Integrate experiment design/results:** reproducible data, reference values, gaps, charts, statistics, interpretation and limitations.
- [ ] **27. Quality assurance:** notebook run-all tests, environment/data dependency manifest, references, coherent storytelling, clean figures, code performance/comment readability, final conclusions.

**Milestone:** final project deliverable, **the day before the defense**.

### Phase 7 — English oral defense

- [ ] **28. Build presentation** with context, objectives, core CVRP formulation, algorithm, results, risks, limitations, accomplishments and future schedule.
- [ ] **29. Live demo** using small instances so execution is fluid; demonstrate loading, optimization, feasibility and route visualization; prepare fallback screenshots/results.
- [ ] **30. Team rehearsal and submission:** divide responsibilities among four members, practice English explanations and anticipated questions, verify final deliverable, conduct oral defense.

**Milestone:** presentation on the last day of the academic block. The brief also mentions an ADEME July 12 submission (exact year/relationship to academic dates needs confirmation).

---

## 11. Performance evaluation and statistical protocol

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

### 11.1 Mandatory minimum

- **At least 20 distinct instances**. Repeated runs on one instance are valuable but do **not** count as distinct instances.
- **VRPLIB** parsing via `vrplib` for classical references; validated category-specific advanced loaders and references only when objectives/constraints match (A6).
- Cost and execution time measurements; experiments across different instance characteristics; visualization and statistical discussion.
- Robust reproducibility: seeds, dependency versions, hardware and resource limits.

### 11.2 Suggested scenario factors (proposed, not grading thresholds)

| Scenario type | Illustrative ranges/settings | Purpose |
|---|---|---|
| Small | 20–100 customers | Debugging, potential exact comparisons |
| Medium | 100–500 customers | Neighborhood/operator effectiveness |
| Large | 500–1000 customers | Runtime and search scalability |
| Very large | 1000+ customers | Investigate requirement ambition “several thousand” |
| Geography | Uniform, clustered, mixed | Spatial-structure sensitivity |
| Demand/capacity | Low/moderate/high capacity pressure | Feasibility and algorithm difficulty |
| Fleet | Different $K$, documented bound source | Fleet usage vs route quality |
| Metaheuristic | Seeds, iteration/runtime budgets, removal fraction, acceptance, neighborhood size | Robustness and tuning |

Ranges are **experimental categories**, not fixed caps built into code. The experiment plan should define actual supported instances and distinguish tuning vs evaluation data.

### 11.3 Required and useful output metrics

- Instance ID/source and characteristics: $n,K,Q$, total demand, demand distribution, coordinates type, reference value and status (optimal/BKS).
- Feasible solution: yes/no, vehicle count used, routes, load per route.
- Best observed total distance from **our algorithm** (when implemented).
- Initial solution cost and relative improvement.
- Best/mean/std/worst final cost across repeated runs, optional quartiles/confidence bands.
- Runtime, including clear exclusion/inclusion of data loading and plotting.
- Gap (%) and whether its reference is proven optimal or only BKS.
- Termination reason, time budget, number of iterations, software/hardware, random seed.
- Sensitivity analysis and explainable limitations.

### 11.4 No unsupported benchmark claims

The modeling notebook validated the **published A-n32-k5 reference route** with cost 784. That does **not** establish that the team's future algorithm finds 784 or any particular gap. All claimed algorithm performance must come from the actual future solver experiment and recorded conditions.

---

## 12. Architecture, reproducibility, testing and team work

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

### 12.1 Proposed repository structure

```text
EcoRoute-CVRP/
├── README.md
├── context.md                  # This context handoff
├── requirements.txt            # To create
├── notebooks/
│   ├── 01_cvrp_modeling.ipynb   # Previously produced under a different filename
│   ├── 02_cvrp_algorithm.ipynb  # To build
│   └── 03_experiments.ipynb     # To build
├── src/
│   ├── instances.py            # To build/extract if useful
│   ├── feasibility.py          # To build/extract if useful
│   └── solver.py               # To build
├── data/
│   ├── synthetic/              # To populate
│   └── vrplib/                 # To populate; follow dataset usage terms
├── results/                    # To populate
├── figures/                    # To populate
├── references/                 # Optional
└── presentation/               # To create
```

Production-grade modularity is **not mandatory** per assignment. The directory layout is optional; readability, reproducibility and performance are essential.

### 12.2 Already mentioned libraries and tooling

- Python, Jupyter Notebook/IPython.
- `numpy`, `pandas`, `matplotlib` for validation, numerical data and plots.
- `vrplib` for CVRP benchmark reading.
- `dataclasses`, `pathlib`, `math`, `collections.Counter`, `re` and standard Python utilities in recorded notebook.
- A future optimization algorithm can rely on Python scientific tools and carefully designed incremental update operations; no solver library has yet been required or chosen.
- Optional exact ILP packages mentioned in prior explanatory answers: Gurobi, CPLEX, CBC, but **not** implemented and not compulsory for first modeling check.

### 12.3 Testing checklist

- Validate matrix shape, demands, depot, fleet and numerical domains.
- Verify objective cost equals sum of selected route arcs.
- Verify all customers served exactly once, no duplicate/missing labels, capacity constraints, route starts/ends at depot and disconnected subtours excluded.
- Explicitly test zero-demand customers, a customer at capacity, unused trucks, insufficient aggregate capacity, bin-packing counterexamples, one vehicle and one customer, asymmetric and nonmetric distances where supported.
- Check route checks on both hand-written candidate and published reference solutions; never assume a reference route is a solver output.
- Record random seeds; ensure any future numerical tests are deterministic when requested.
- Test algorithm moves and statistics separately once implemented.

### 12.4 Suggested four-person division of work (not assigned to named individuals)

1. **Math/formalization lead:** assumptions, ILP, NP-hardness, correctness, tutor feedback.
2. **Algorithm lead:** initial construction, neighborhood/local search, metaheuristic.
3. **Data/benchmark lead:** VRPLIB, instance metadata, validation, experiments and statistics.
4. **Integration/documentation lead:** notebooks, figures, presentation coordination and reproducibility.

All team members should understand the model, participate in review/testing, and speak during the final presentation as assigned.

---

## 13. Sources and references

See [`sources.md`](sources.md) for the original French assignment, user-supplied URLs, scientific literature, and benchmark documentation.

---

## 14. Chronological user prompts and explicit instructions

> **Purpose:** preserve the actual user's instructions so later assistants do not mistake an assistant's suggestion for a user requirement. The original long French prompt is preserved substantially verbatim in [`sources.md`](sources.md) and referenced rather than duplicated here. Original spelling/capitalization is retained where visible. Chronology is the visible conversation order; not every message carried an explicit timestamp.

### Earlier messages from the related CESI-PROJECT conversation (source: project-history excerpt)

The project context also includes an earlier discussion titled **“Optimisation des tournées de livraison”** (2026-10-21). The following user messages from that discussion are preserved because they establish important project-quality requirements.

> Create the detailed CVRP mathematical modeling Jupyter

*The preceding prompt is only shown as a truncated excerpt in project history; do not claim it is verbatim complete.*

> did you only do the modeling part? explain what you did so far

> Before I review, just let me know what you've done. Write a brief summary of what you've done. What do you mean by modeling, and also what parameters are modifiable? Go ahead, let me know. Be very concise.

> make a detailed README about what needs to be done , with steps , TODOs, what has already been done, what is yet to be done, if there are things that need validation/ research / approval from me, mark them, KEEP IN MIND WE MUST NOT IGNORE ANY DETAIL, ALL THE THINGS I'VE TOLD YOU TO TURN INTO VARIABLE PARAMETERS,  ALL THE POTENTIAL DETAILS THAT THE PROFESSORS COULD ASK US ABOUT, LEAVE NOTHING TO RANDOMNESS, DONT BE LAZY, no matter how long the run takes, EVEN THE ALGORITHM MUST BE AS OPTIMAL AS POSSIBLE, WE'VE DONE THE MODELING SO FAR, SO NOTE ALL THE NEXT STEPS

> i want you to review the implementation plan for mistakes, the thing we must avoid at all costs, is a bad algorithm or a non optimal one, and missng details, review it go ahead

**Interpretation:** The user requires rigorous **algorithm comparison, parameterization, edge-case coverage and critical reviews**; they do not want an arbitrarily selected or poor-performing heuristic. “As optimal as possible” is a performance goal, **not proof that a metaheuristic can always find the optimum**.

### Prompt 1 — Original French assignment (full text: `sources.md`)

User pasted the environmental ADEME/CesiCDP statement and assignment with official links, versions, deliverable requirements, evaluation and VRPLIB reference. **See [`sources.md`](sources.md) for the original user-supplied assignment text**.

### Prompt 2 — Language instruction

> answer in english neve i french, start over

**Effect:** response/documentation language English; only the archived original assignment stays French.

### Prompt 3 — Question about final corrected ILP

> what do they lmean byt htat modélisation mathématique sous forme de Programme Linéaire en Nombres Entiers (PLNE) complète et corrigée,
>
> -

**Effect:** clarify that final PLNE must have decision variables, objective, complete constraints, correct subtour logic, and corrections after tutor review.

### Prompt 4 — Begin with CVRP variables, objective, constraints, conditional code

> so in our modeling we must have a set of potential decisions that the algorithm can make , an objective function (like a cost function we have to minimize) and a set of constraints we have eto follow, lets start with that problem, what are the constraints, objectiv efuction, for now oNLY WORK ON THE CVRP not the advanced version, and give a python implementation of it, ipynb script  (IF REQUIRED BY THE ENONCÉ)

**Effect:** CVRP only; modeling includes decision variables, cost function and constraints; first check excludes a required optimization solver.

### Prompt 5 — End-to-end checklist and full parameterization

> break up the project into steps, like a to do list, explain what step we're at right now, give details, MAKE SURE TO INCLUDE EVERY STEP, we musgt also have a lot of parameters like capacity etc like we mustnt fix anything

**Effect:** comprehensive plan and parameterized model/implementation, no hard-coded capacities/fleet counts/customer counts.

### Prompt 6 — Highly detailed notebook with plots; ask before starting

> go ahead, make a ipynb script, with A LOT OF PLOTTING and HIGHLY DETAILED COMMENTS, DO NOT MISS ANYTHING, for now only do the modeling, go ahead ask me questions before you start

**Effect:** high-detail, visualization-rich modeling notebook; assistant then clarified objective, data and code scope.

### Prompt 7 — All notebook choices explicitly confirmed

> Create the detailed CVRP mathematical modeling Jupyter Notebook (.ipynb) now. Confirmed decisions: primary objective = distance for VRPLIB benchmark compatibility; data = both synthetic examples and VRPLIB benchmarks; Python modeling code = plots, instance parsing, constraint illustrations, and feasibility checks, but no optimization solver. Include complete parametrized CVRP ILP, all necessary constraints and subtour elimination, rigorous complexity proof, extensive explanations and comments, many meaningful visualizations, academic references, and a verified downloadable .ipynb file.

**Effect:** authoritative final specification of the first modeling deliverable, replacing ambiguous prior defaults.

### Prompt 8 — Status question

> did you only do the modeling part? explain what you did so far

**Effect:** explicitly distinguish modeling code/plots from actual optimization algorithm implementation.

### Prompt 9 — Concise progress and configurable parameters

> Before I review, just let me know what you've done. Write a brief summary of what you've done. What do you mean by modeling, and also what parameters are modifiable? Go ahead, let me know. Be very concise.

**Effect:** record the definition of modeling and clearly list configurable input fields.

### Prompt 10 — Project name

> give a name to the project

Assistant proposed “EcoRoute — Intelligent Delivery Route Optimization.”

### Prompt 11 — GitHub repo name

> for a github repo

Assistant proposed `EcoRoute-CVRP`, description: *A Python-based Capacitated Vehicle Routing Problem (CVRP) optimization project featuring mathematical modeling, metaheuristic algorithms, route visualization, and VRPLIB benchmarking*. Suggested URL was `github.com/your-username/EcoRoute-CVRP` — an example URL that requires the actual account name.

### Prompt 12 — Exhaustive context document (previous instruction)

> i want you to basically give me back all the ressources i gave you at the start of the conversation, the enoncé, the sources, the prompts telling you what to do, and compile them in a context.md file , DO NOT OMIT ANYTHING IT NEEDS TO HAVE EVERYTHING THERE IS TO KNOW ABOUT THE PROJECT, DONT LEAVE ANY DETAIL, FIRST I WANT YOU TO MAKE A LIST OF EVERYTHING THERE IS TO KNOW ABOUT OUR PROJECT, LEAVE NO STONE UNTURNED

**Effect:** compile the complete inventory, original assignment, user sources, chronological prompts, decisions, work status, parameters and roadmap in one file.

### Prompt 13 — Detailed accuracy review request (2026-11-02)

> verify what you wrote, any mistakes or things you would correct? the file needs to be 10000% accurate, no minor mistakes review it for mistkaes and minor upgrades/ corrections, CHECK EVERYTHING

**Effect:** improve mathematical and project consistency, benchmark interpretation, terminology, completeness and detail before sharing the file.

### Prompt 14 — Request for a ranked explanation of project issues

> Okay just rank them from most important to least important. And tell me what you're talking about give more context about each issue documentation

**Effect:** clarify which technical modeling and project risks have the greatest effect on correctness, benchmarks and grading.

### Prompt 15 — Shared context-document editorial instruction (2026-11-02)

> The context can include every source that we've had in order to make the project work but don't include those issues about the validity of the sources in your file because it will be shared.

**Effect:** keep original assignment links, scientific references, technical resources and substantive implementation guidance while presenting the document as a clean team-facing context resource rather than an internal source-audit report.

---

## 15. Assistant decisions, suggested approach and corrections

### 15.1 Earlier explanations that are compatible with the assignment

- A PLNE is a discrete mathematical optimization formulation, specifying legal decisions, cost to minimize and explicit feasibility rules.
- It is not the same thing as an implementation of an algorithm to find high-quality routes.
- The first checkpoint explicitly requires **no solver** or discussion of resolution methods. Modeling code that plots and checks candidate routes is acceptable, so long as it does not claim to satisfy the later solver requirement.
- The original longer problem (traffic-dependent time) is not identical to the standard CVRP benchmark. The user selected distance so that reference comparisons make sense.
- The model's $Q,K,n,q_i,d_{ij}$ are parameters. Numeric demonstrations do not fix them globally.
- A complete final PLNE must incorporate tutor corrections and avoid missing subtour constraints.
- The optimization CVRP is NP-hard. The decision version is NP-complete under usual encoding assumptions.

### 15.2 Prior assistant recommendations (not confirmed requirements)

- Historical recommendation: start with a static CVRP baseline. The latest user decision explicitly includes advanced windows and traffic; implement all three layers.
- Use greedy insertion or Clarke–Wright Savings for an initial feasible solution.
- Add 2-opt, relocate, swap, and possibly 2-opt* for local improvement.
- Choose ALNS (adaptive large neighborhood search) as a plausible main metaheuristic; define removal/insertion operators, acceptance and stopping criteria.
- Use `vrplib` and multiple benchmark families; compare to BKS with correct rounding.
- Use a four-person role split and a repository directory organization as suggested in Section 12.
- Make notebook content story-driven, with charts, equations and interpretation.

**These are planning suggestions until approved/implemented.** Do not claim that ALNS is chosen by the user, or that it is already coded. A particularly strong user requirement from the earlier related project conversation is **to critically evaluate alternatives and avoid a weak/noncompetitive algorithm**: compare credible baselines and, where useful, established high-performance approaches (e.g. hybrid genetic search) before finalizing the metaheuristic. ALNS is not proven best by this project record.

### 15.3 Clarifications and potential corrections to keep visible

- **At most $K$ versus exactly $K$:** current model allows unused trucks. Confirm with tutor if exactly $K$ required. Importantly, the *minimum vehicles* field on CVRPLIB is neither interpretation by itself; benchmark comparison must respect the original benchmark constraints.
- **PLNE versus MILP terminology:** if $u$ is continuous, MILP; if integer, all-integer PLNE. Both describe a mixed discrete routing formulation; specify domains consistently.
- **Reference gap terminology:** using a BKS denominator does not certify optimality.
- **Time vs distance:** duration/traffic is now in the selected Layer 3 target; retain distance comparisons only under Layer 1 conventions.
- **Date precision:** original text supplies “July 12 next” and relative academic milestones; the calendar year must be set from the official project schedule.
- **Large instances:** an exact three-index ILP is a valid specification, but cannot be assumed tractable at thousands of nodes.
- **Reference data:** benchmark routes in the notebook were not generated by our solver.
- **Graph symmetry:** no universal need for $d_{ij}=d_{ji}$, unless an instance specifically provides symmetric Euclidean costs.
- **Feasibility:** $KQ\ge\sum_i q_i$ does not alone imply feasibility due to indivisible deliveries.
- **Degree conditions:** without MTZ or equivalent connectivity cuts, separate customer cycles could satisfy local flow equations but be invalid routes.

---

## 16. Open questions, risks, limitations and next action

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

### 16.1 Questions to settle with the tutor/team

1. **Does the final CVRP require at most $K$ vehicles, or exactly $K$ used vehicles?**
2. Does the proposed total-elapsed-time objective and its flexible-departure/holding policy match tutor expectations for Layer 3?
3. Which official datasets are supplied by CESI (file links, instance families, fleet metadata, cost rules), if any beyond the explicitly linked `vrplib` repository?
4. Which algorithm/metaheuristic will the team implement — ALNS or another method? **What evidence/baselines justify its quality and robustness?**
5. What runtime or iterations budget, hardware, seeds and repetitions define a fair experimental protocol?
6. What is the exact submission **year** for July 12 and the actual dates of Prosit 3, final notebook and defense?
7. Which benchmark costs are **proven optimal** and which are **BKS**?
8. Do instances include customer demands of zero, asymmetric road costs, non-Euclidean matrices, fleet constraints or other special conventions?
9. Are there any further tutor corrections to the mathematical constraints/notation?
10. Which teammates own implementation, experiment review, report integration and English presentation?

### 16.2 Risks to monitor

- Incomplete subtour constraints produce mathematically invalid “solutions.”
- Inconsistent rounding yields false reported gaps.
- Confusion between a known reference route and algorithm performance yields unsubstantiated results.
- Treating unprovided fleet metadata as a magic constant undermines reproducibility.
- Testing the same instance 20 times does not satisfy **20 different instances**.
- No benchmark budget controls or seeds makes stochastic comparisons unfair.
- Performance bottlenecks of quadratic dense matrices and expensive local-search operations may make thousands-of-customers ambition difficult.
- Claiming an exact optimum without a certificate or authoritative reference is incorrect.
- Late tutor feedback could require changing fleet semantics or objective.

### 16.3 Immediate action, in order

1. **Review the modeling notebook** and check equations plus the notebook's reported execution on your machine. This context file is not a substitute for the actual `.ipynb`.
2. **Validate with tutor**: fleet semantics, scope/objective, model assumptions, NP-hardness reduction and complete PLNE.
3. **Record tutor corrections** and revise the notebook/model accordingly.
4. **Design/configure instance-loading and solver interfaces** (dynamic $n,K,Q,q,d$ and benchmark metadata).
5. **Implement** the chosen initial heuristic, local search and metaheuristic in the next deliverable, then test and benchmark on at least 20 distinct instances.

---

## 17. Project artifacts and current deliverable status

### 17.1 Verified artifacts and historical names

The actual inspected files and missing historical artifacts are listed in A8. The only existing notebook is `CesiCDP_CVRP_Modeling.ipynb`; it is a classical CVRP modeling draft, not a TD-CVRPTW solver. `README.md`, `context.md`, `sources.md` and `CVRP_Implementation_Plan_Audit.md` are the project documentation. The animation guide is unrelated and unchanged. Earlier detailed/mathematical notebook names, ZIP, standalone `.vrp`/`.sol` and short README are historical references, not present files. The directory tree in Section 12 is a proposal.

### 17.2 Delivery status

- **Mathematical modeling:** detailed draft notebook produced; tutor checkpoint and any requested corrections remain outstanding.
- **Route optimization:** no initial-solution search or ALNS implementation completed in the recorded project progress.
- **Experiments:** no 20-instance algorithm-comparison study completed yet; published reference-route examples were used to check the model, not to measure a new solver.
- **Final notebook and English defense:** planned for the later milestones.
- **Repository:** the existing remote is https://github.com/DennixAI/EcoRoute-CVRP; review upgrades on branches via PRs.

For each future milestone, record the completion date, responsible team member, acceptance criteria, and links to its deliverables.

---

## 18. Tutor defense preparation checklist

**Layer applicability:** preserve the classical baseline details below and apply A1–A8 to the advanced target. Temporal inputs, traffic evaluation, schedule feasibility and stratified experiments are mandatory additions to this workstream.

These are preparation questions derived from the mathematical model, technical requirements and planned experiments; they are not additional grading rules:

- [ ] Precisely state the basic CVRP scope, one-depot assumption, no split deliveries, fixed distance objective, and how Layers 2/3 add time windows, waiting and predicted traffic (A1–A4).
- [ ] Explain every index and variable ($x_{ijk}$, $y_{ik}$, $z_k$, $u_{ik}$), variable domain, and which values are inputs rather than hard-coded constants.
- [ ] Derive the objective and justify including departures and returns; distinguish total fleet distance from maximum route duration and fleet count.
- [ ] Explain why degree/flow equations alone allow disconnected subtours, and demonstrate the MTZ cycle contradiction.
- [ ] Justify the exact $(n+1)$ big-$M$ coefficient and the order-variable bounds, including zero-demand clients.
- [ ] Prove both directions of model correctness: legal routes ⇒ feasible variables, and feasible variables ⇒ legal routes.
- [ ] Give a valid TSP-to-CVRP polynomial reduction; distinguish NP-hard optimization from NP-complete decision problems.
- [ ] Explain exactly-$K$, at-most-$K$, and CVRPLIB **minimum vehicle count** as different concepts.
- [ ] Explain individual-demand and aggregate-capacity necessary bounds, and why they are not sufficient (bin packing).
- [ ] Explain distance parsing for `EUC_2D`, explicit matrices, nearest-integer reference conventions and why mismatches invalidate reported gaps.
- [ ] Explain **optimal** versus **best-known** references, how negative BKS gaps can arise, and how to verify reference-route feasibility.
- [ ] Justify the chosen metaheuristic with comparisons, neighborhood design, acceptance strategy, runtime/memory considerations, and evidence that it is competitive. **Never claim global optimality from a stochastic solver without proof.**
- [ ] Explain experiment reproducibility (at least 20 different instances, repetitions, seeds, budgets, CPU/hardware), proper statistics, and tuning/test separation.
- [ ] Explain scaling to thousands of customers: why the explicit MILP has $O(Kn^2)$ arc variables, why a dense $n\times n$ `float64` distance matrix uses approximately $8n^2$ bytes, and when sparse/on-demand costs are appropriate.
- [ ] Explain environmental motivation while acknowledging **distance is a proxy**, not an independently measured carbon-emissions model.
- [ ] Explain what has actually been coded, what has only been modeled, what requires tutor approval, and what experimental claims cannot yet be made.


---

## Final scope reminder for future contributors and AI assistants

**Current target:** Layer 3 TD-CVRPTW with capacity, hard customer windows, waiting and predicted traffic, using the time-based objective in A2. Layers 1/2 remain validation baselines. Only a classical modeling notebook currently exists. Advanced notebook work, solver, benchmark experiments and tutor review remain pending. Follow A1–A8 and preserve at least 20 distinct final evaluation instances.
