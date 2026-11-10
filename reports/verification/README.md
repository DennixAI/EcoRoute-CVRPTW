# Final CVRPTW infrastructure verification

**Infrastructure: PASS. No optimization algorithm was implemented, prototyped, selected or benchmarked.**

| Check actually executed | Result | Evidence |
| --- | --- | --- |
| Automated unit/integration suite | 33 tests PASS | [Test log](20261109-final/unit-tests.log) |
| Every native benchmark/reference pair | 356 PASS, zero failures | [Per-instance CSV](20261109-final/instances.csv), [full JSON](20261109-final/verification.json) |
| C101 independently reconstructed score | 827.3, matches publication | CSV and integer-square-root unit test |
| GH200/C1_2_1 score | 2698.6, matches publication | Per-instance CSV |
| Fresh notebook execution | All 25 code cells executed; no errors | [Execution record](20261109-final/notebook-execution.json), `outputs/main.executed.ipynb` |
| Repeated reference campaign | 20 distinct test fixtures × 2 seeds, plus 1 disjoint development fixture × 2 seeds; 42/42 feasible, zero replay gaps | [Campaign manifest](../../results/20261109-verified-reference-fixture/manifest.json), [comparison](../../results/20261109-verified-reference-fixture/comparison.md), [runs CSV](../../results/20261109-verified-reference-fixture/runs.csv) |
| Assertions disabled | Corrupt temporal schedule and disconnected zero-time/zero-demand subtour rejected under `python -O` | Command below, also covered in ordinary suite |
| CLI path independence | Modeling, verification, benchmark and downloader help run outside repo; external invalid/missing outputs persisted correctly | Integration suite |

A zero reference replay gap only verifies the evaluator. Its algorithm-quality assessment is **NEEDS IMPROVEMENT / no executed solver evidence**, with unknown solver runtime/budget explicitly recorded. No target-quality claim, optimization experiment, BKS improvement or proof of optimality is made. No real network re-download or PyVRP baseline execution was performed.

## Corrections and boundaries

- Corrected the notebook's full continuous-variable count to **4Kn+2K** (waiting derived), and clarified the arc-variable chart. Mathematical model structure and plotting code remain intact; stale source outputs were cleared, with fresh executed outputs stored separately.
- Established the authoritative frozen `CVRPTWInstance`: owned read-only arrays, required windows/service, separate static distance and travel matrices, external node/depot mapping, scoring policy and benchmark metadata. Shared boundaries reject the older capacity-only teaching container. Its notebook validator explicitly rejects CVRPTW objects so windows cannot be silently ignored.
- Validated IDs across coordinates, demands, windows and service sections; rejects malformed/missing fields and bad scalar/vector service. Added safe coordinate checks, total integer-tenths cost accumulation, nonfinite-total rejection, and strict tolerance/departure handling. Capacity/window/depot residual magnitudes remain in schedules/totals.
- Retained MTZ with n+1, including a test that all other routing constraints accept a disconnected zero-time/zero-demand cycle while MTZ rejects it. Temporal residual checks now remain active under Python -O. Reviewed earliest-schedule sufficiency, service-start versus completion, finite H+t big-M and active/inactive vehicles. No MILP solver or formal machine proof was added; tutor sign-off is still required.
- Collection checking retains every available pair's failure instead of stopping at the first one. Incomplete normal runs are NOT RUN only when available data are valid; malformed available pairs remain FAIL. Strict failures carry the complete report.
- Added independent offline evaluation and a future adapter API, hard wall deadlines, distinguishable errors/crashes/timeouts/no-solution/invalid routes/missing references, and actual measured timing boundaries. Test doubles only replay supplied routes, raise exceptions, crash deliberately or wait; none constructs/improves a route.
- Added disjoint development/test plans, repeated seeds, every planned attempt (including omissions), positive independently verified BKS denominators, independent gaps, cost disagreement and negative-gap review flags, configurable quality thresholds, per-instance/family statistics, paired exploratory bootstrap, tables and a checked comparison PNG.
- Results persist with unique campaign/run IDs, atomic exclusive JSON publication, flushed run ledgers, saved routes/config/schedules/logs/traces, code/dataset/reference checksums, exact evaluator sources, hardware and dependency versions. Prior campaigns are retained, not overwritten. Long-term off-device retention still needs a policy.
- Unified default data paths at `data/benchmarks/vrptw`, with configured roots on all CLIs and `--destination` on the downloader. Documentation links now reflect the user's cleanup; context/dataset/benchmarks and deleted modeling-audit files were not recreated. Original CESI requirements remain in synchronized AGENTS.md/CLAUDE.md.

## Reproduce

From an environment installed with repository requirements.txt (Python 3.9.6 actually tested):

```bash
python -m unittest discover -v
python -O -m unittest tests.test_model.ModelTests.test_temporal_corruption_and_mismatched_routes tests.test_model.ModelTests.test_subtour_zero_demand_and_time -v
python scripts/verify_dataset.py --output reports/verification/your-new-id
python scripts/run_modeling.py --strict
python scripts/run_benchmarks.py --reference-fixture --output results/your-new-id
```

Use a NEW directory ID each time; existing evidence is protected from overwrite. [Full verified environment freeze](20261109-final/requirements-verified.txt). Exact evaluator snapshots accompany each campaign/report, including earlier verification runs. The recorded dataset collection SHA256 remains `73cc107742d4d73761df1b92f204c62010198c575d1f40af73afb0bbca1a0549`; source manifest/archive hash are preserved. Upstream main's precise Git commit was not recorded originally and has not been invented.

## Unresolved decisions

1. Tutor confirmation of selected static minimum-distance, service-start-window, mandatory-all-customer and at-most-K scope against the original traffic/duration narrative, plus final model/proof review. Actual course dates, team roles, submission language/format still need confirmation.
2. Future genuine held-out instance IDs, repeat count (proposed 10 seeds; minimum 2), budgets per size, hardware/thread/CPU-affinity/memory controls, tuning fairness, statistical comparison plan and timeout/incumbent policy. Fixture splits are not a final sealed test set.
3. Pin and verify a future PyVRP baseline/environment; no baseline solver dependency or chosen algorithm exists. Settle allowed external-code/academic originality expectations before implementation.
4. Durable off-device archive/retention policy for large campaigns; resource-limit enforcement and streaming incumbent recovery are not implemented. Abrupt workers are distinguished from timeout, but a hard-killed worker yields no incumbent. No resume CLI exists; completed per-attempt evidence survives interruption.
5. Several-thousand-customer stress testing if the tutor requires it: the native collection stops at 1,000, and no larger-scale performance evidence exists.

The mandatory infrastructure completion condition is satisfied: all supported native inputs load, supplied routes can be independently validated, published costs reproduce, and correct gaps can be computed without an optimizer. Algorithm development stops here.
