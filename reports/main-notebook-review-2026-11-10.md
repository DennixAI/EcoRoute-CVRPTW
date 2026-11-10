# Review of `main.ipynb` — 2026-11-10

> **Status (later on 2026-11-10):** findings 1–6 were resolved in commit `d2942d4` (notebook-only solver with rebuild/re-import, Numba pinned and checked, deterministic demo, corrected wording and titles). Findings 7–12 remain open. The text below is the review as written.

Scope: every one of the 101 cells of `main.ipynb` as on `main` at `a73308e` (identical to branch `claude/cvrptw-alns-vnd-4fa707`), read together with a fresh strict execution (`scripts/run_modeling.py --strict`). Suspected problems were checked with small experiments; the evidence is given with each finding. Nothing was changed in the notebook or the code for this review.

Cell numbers below are 0-based positions in the notebook (`[n]`), followed by the section.

## Verdict

The notebook executes end-to-end in strict mode with no errors (≈46 s), all assertions hold, the 356 reference pairs validate, and the mathematical model is sound for the selected scope. **No error was found in the MILP, the complexity argument or the benchmark numbers.** The findings are about (a) two real defects in the new ALNS loader/demo workflow, (b) statements that are now out of date, and (c) presentation and methodology points worth fixing before the defence.

| # | Severity | Finding | Where |
| --- | --- | --- | --- |
| 1 | **High** | Without Numba the demo silently runs pure Python and shows an 11.5 % gap; setup text never asks for Numba | [2] §0, [89] §15.1, [93] §15.3 |
| 2 | **High** | `load_alns()` can run stale code while reporting "verified identical" | [59] §12 |
| 3 | Medium | The live demo is not reproducible although it fixes a seed | [93] §15.3 |
| 4 | Medium | "Precompiled, about a second" is false on a fresh clone (≈16 s+ compile) | [58] §12, [88] §15.1 |
| 5 | Medium | Several statements are out of date now that ALNS is in the notebook | [0], [2], [3], [28], [43], metadata |
| 6 | Medium | Demo budget described as "a third of the benchmark budget" — true only at 100 customers | [92] §15.3 |
| 7 | Low | Section numbering gaps and an empty section | [41], [51], [60]/[62] |
| 8 | Low | Results interpretation hard-codes numbers that the cells above compute | [98] §15.5 |
| 9 | Low | Insertion pruning assumes the triangle inequality, which DIMACS truncation breaks | solver cell kernels 6 (§13.6) |
| 10 | Low | Two parallel validators/instance types can confuse readers | [8], [30], [38] vs [53]–[56] |
| 11 | Low | Model-size table omits some constraint families | [44] §8.2 |
| 12 | Info | Methodological limits of the reported PASS | [95]–[98] §15.4–15.5 |

---

## 1. High — the demo degrades badly without Numba, and nothing says Numba is needed

* **What.** Section 0 [2] tells the reader to install `numpy pandas matplotlib vrplib` (and the notebook-execution packages). `requirements.txt` does not contain Numba; it is only in `algorithms/alns_vnd/requirements.txt`. Without it, `_jit.py` falls back to plain Python. Cell [89] only prints `Numba JIT enabled: False`; nothing warns.
* **Evidence.** Same demo call (`solve(..., seed 0, 10 s)`) with `ECOROUTE_DISABLE_JIT=1`:

  | Instance | Iterations (pure Python) | Gap | With Numba |
  | --- | ---: | ---: | ---: |
  | Solomon/R102 | 345 | 0.00 % | ≈42,000 iterations, 0.00 % |
  | GH400/R1_4_10 | 67 | **11.5 %** (cost 9010.2 vs BKS 8077.8) | ≈14,500 iterations, 1.4–2.4 % |

  The time limit is still respected (9.1 s), but construction alone takes 3.7 s at 400 customers and would exceed a short limit at 1,000 (construction is not interruptible).
* **Impact.** On a machine set up from the notebook's own instructions — e.g. the defence laptop — the live demo would show a gap above the 7 % investigation threshold, contradicting the 0.654 % headline.
* **Fix.** List `algorithms/alns_vnd/requirements.txt` (or `numba`) in §0 and the README setup; in [89] raise a clear warning (or stop in strict mode) when `JIT_ENABLED` is false; optionally merge `numba`/`psutil` into `requirements.txt`.

## 2. High — `load_alns()` can execute stale code while claiming it is verified

* **What.** [59] compares the notebook cells with `algorithms/alns_vnd/*.py` on disk and, if identical, calls `importlib.import_module("algorithms.alns_vnd")`. If the package was already imported earlier in the same kernel, Python returns the cached module from `sys.modules`; the files are not re-read.
* **Evidence.** Import the package, change `solver.py` on disk, call `import_module` again: it returns the *same object* with the *old* `VERSION` (reproduced with a temporary copy of the package).
* **Realistic trigger.** Run All (precompiled path, package imported) → edit a solver cell → `load_alns()` compiles the notebook version (correct) → run `scripts/sync_notebook_solver.py --write` → re-run `load_alns()`: cells and files now match, so the *pre-edit* module is returned and the demo runs old code under the message "verified identical to these cells".
* **Fix.** In the precompiled branch, drop `algorithms.alns_vnd*` from `sys.modules` (or `importlib.reload` each submodule in dependency order) before importing, or compare the loaded modules' source hashes with the cells. Restarting the kernel avoids it today.

## 3. Medium — the live demo is not reproducible despite `DEMO_SEED = 0`

* **What.** The search stops on wall-clock time and the annealing temperature follows elapsed time, so iteration counts and results differ between runs with the same seed.
* **Evidence.** GH400/R1_4_10, seed 0, 10 s: 8247.7 / 8246.6 / 8276.1 in three consecutive runs (2.09–2.45 %); the four notebook executions today gave 1.37 %, 1.84 %, 1.94 % and 2.40 %. With an iteration budget (`{"max_iterations": 3000}`) two runs gave the identical cost 8389.8.
* **Impact.** Numbers shown at the defence will not match the saved notebook, and a fixed seed suggests they should.
* **Fix.** State in [92] that time-limited results vary run to run, or offer a deterministic demo mode (`max_iterations`) and say which is used.

## 4. Medium — "precompiled, about a second" is not true on a fresh clone

* **What.** Numba's cache files (`*.nbi`, `*.nbc`) are git-ignored. After a clone, or after any change to the `.py` files, the "precompiled" branch still compiles everything during the warm-up.
* **Evidence.** Warm-up with an empty cache (`NUMBA_CACHE_DIR` set to an empty directory): 15.7 s; with a warm cache: 0.4 s (0.1 s inside the notebook). Some functions only compile when first used, so part of the cost can also land in the first demo run.
* **Impact.** Misleading text in [58] and [88]; the first demo after cloning starts slowly.
* **Fix.** Say "after a one-time compilation (≈15–60 s)"; recommend one Run All before presenting; optionally make the warm-up exercise every destroy/repair operator.

## 5. Medium — out-of-date statements

| Cell | Current text | Problem |
| --- | --- | --- |
| metadata `title` | "CesiCDP – CVRP Mathematical Modeling (Checkpoint 1)" | Problem is CVRPTW; notebook now also contains the algorithm and results |
| [0] | "Deliverable 1 — capacity, hard service-start windows and visual validation" | Same |
| [2] §0 | install list; "reference checking uses no randomness" | Misses Numba (finding 1); the ALNS demo is randomised (seeded) |
| [3] | "No optimization solver or metaheuristic package is imported." | True for packages, but the notebook now contains its own metaheuristic; reads as contradictory |
| [28] §5 | "Heuristic or metaheuristic research belongs to a later phase; none is chosen here." | ALNS + VND is implemented in §12–15 |
| [43] §8.2 | "…should later use an efficient heuristic for large instances" | Now done — point to §12 |

## 6. Medium — demo budget description is inaccurate

[92] says the 10 s default is "a third of the 0.3 s/customer benchmark budget". The benchmark limits are 30 s (100 customers), 60 s (200) and 120 s (400), so 10 s is ⅓, ⅙ and ⅟₁₂ for the four demo instances. Say "10 s per instance, i.e. ⅓–⅟₁₂ of the benchmark budget, so gaps are higher than in §15.4".

## 7. Low — numbering and structure

* There is no Section 7: §6 [29] is followed by §8 [41].
* §10 [51] is a heading with one paragraph and no cells; the content is in §10A [52].
* §12.1 and §12.2 ([60], [62]) document `_jit` and `config`, while the kernels are §13 and the driver §14; consider §12.1–12.2 → "Solver configuration" under one heading or renumber 12–15 consistently.

## 8. Low — hard-coded results in the interpretation

[98] repeats 0.654 %, 2.364 %, 0.3 %→1.2 % etc. as text. They are correct for `test-001`, but they are computed live in [96]; if the campaign is re-run, the text silently goes stale. Either mark it explicitly as "campaign test-001 (frozen)" — it does — and keep it, or generate the sentence from the loaded tables.

## 9. Low — insertion pruning relies on the triangle inequality

`best_insertion` (§13.6) stops scanning a route once the customer cannot be reached in time from the current node, assuming later nodes cannot reach it sooner. DIMACS truncation violates the triangle inequality in 0.15–0.34 % of node triples (Solomon/R102 0.335 %, GH400/R1_4_10 0.218 %, GH1000/RC2_10_6 0.154 %; largest shortcut 0.1). The pruning can therefore occasionally skip a feasible insertion. This never creates an infeasible solution (every move is checked) and the effect on quality is negligible, but the code comment says "metric travel" and the notebook markdown says only "stops early" — mention the assumption.

## 10. Low — two validators and two instance types

The teaching container `CVRPInstance` and `validate_routes` ([8], [30]) ignore time windows, while `CVRPTWInstance`/`check_cvrptw` ([53]–[56]) are the real ones. This is documented and the teaching checker refuses CVRPTW instances, but a reader skimming §6 can think capacity-only validation is what the solver results use. Consider a one-line note in §6 pointing to §10A as the validator used for every ALNS result, and that `certify_model_equations` checks M1–M10 only (temporal equations are checked by `check_temporal_equations`).

## 11. Low — model-size table is partial

`model_sizes` [44] counts variables correctly (binary $K(n+1)^2$, continuous $4Kn+2K$, matching §8.2) and the temporal-arc inequalities $2Kn(n+1)$ correctly, but omits $y_{ik}\le z_k$ ($Kn$) and the TW1–TW3 bound/definition families ($O(Kn)$). The table is labelled "major constraint families", so this is not wrong, but the asymptotic statement would be clearer with a "+ O(Kn) bound constraints" row.

## 12. Info — limits of the reported PASS (for the defence)

These are correctly stated in the notebook or the results README; listed so the presentation does not overstate:

* PASS is the shared evaluator's verdict for **solution quality** under a budget we chose (0.3 s/customer); no project runtime budget is agreed and no runtime PASS is claimed.
* Gaps are to **published best-known** solutions, not proven optima; no lower bound is computed.
* 36 held-out instances, 6 per size family and 6 per class: family/class means are based on 6 instances each and have no confidence intervals in the notebook.
* Timings come from 6 concurrent workers on one laptop; budgets were respected under that contention.
* No PyVRP baseline at equal budget yet.
* §10A illustrates the published reference routes of Solomon/RC101, which belongs to the test split. That is not leakage (the solver never reads references, and the configuration was frozen first), but it is worth knowing if asked.

## What was checked and found correct

* **Routing model (M0–M10):** degree, depot, capacity and MTZ constraints are complete; the $n+1$ big-M for MTZ is valid; $y_{ik}\le z_k$ is implied by M2–M5 + MTZ and is also added explicitly in §4.5; necessity/sufficiency argument [26] holds.
* **Temporal model (TW1–TW6):** $M_{ij}=H+t_{ij}$ deactivates both sides when $x=0$; service-start semantics, separate $T_k/R_k$, completion after $b_i$ allowed; earliest-schedule sufficiency [27] holds and does not need the triangle inequality.
* **Complexity [28]:** reduction direction (TSP → CVRPTW), horizon, NP-membership argument are correct.
* **Sizing [43]–[44]:** binary $K(n+1)^2$ and continuous $4Kn+2K$ counts match the formulation and are asserted in code.
* **Data and scoring [52]–[56]:** strict audit of all 356 pairs PASS, collection SHA-256 `73cc1077…49`, C101 = 827.3 and C1_2_1 = 2698.6 reproduced, negative cases rejected.
* **ALNS section:** solver cells are byte-identical to `algorithms/alns_vnd/*.py`; the compile-from-notebook path also runs (≈61 s total); every demo result is re-validated by `check_cvrptw`; the loaded tuning and test tables match the committed campaigns (mean gap 0.654 %, worst 2.364 %, 360/360 feasible).
