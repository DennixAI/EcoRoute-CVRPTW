"""Post-hoc ALNS + VND tuning study: NEW experiments on the development split only.

Three experiment sets around the frozen configuration (the notebook defaults):

1. confirmation  historical baseline vs frozen configuration, 5 NEW seeds (2-6)
2. temperature   start temperature 0.25, 0.5, 1.0, 2.5, 4.0 x mean arc (end = start/75), seeds 2-3;
                 1.5 (the frozen value) is the confirmation run's seeds 2-3
3. ablation      frozen configuration minus one destroy / repair operator or VND neighbourhood, seeds 2-3

Every attempt runs through scripts/run_alns.py machinery: isolated worker, hard
wall-clock limit max(10, 0.1 x customers) s (the budget of the historical tuning
campaigns dev-001..dev-007), independent validation and DIMACS scoring by
scripts/benchmark.py. The test and reserve splits are never touched.

All attempts of all campaigns share ONE worker pool (default 8 = the performance
cores of the M2 Max): jobs are queued by experiment set, then longest first, so
no worker idles at campaign boundaries and each set completes before the next.
The solver is frozen once from main.ipynb into tuning-study/solver/ and shared.

    python scripts/alns_tuning_study.py plan
    python scripts/alns_tuning_study.py run [--workers 8] [--only NAME ...]

Resumable: completed campaigns are skipped; interrupted ones are moved aside
(never deleted) and re-run. Progress: results/alns-vnd/tuning-study/progress.log
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_alns import DATA_ROOT, finalize_campaign, launch_job, prepare_campaign  # noqa: E402

OUT = ROOT / "results" / "alns-vnd" / "tuning-study"
SPLIT = ROOT / "results" / "alns-vnd" / "split.json"
NEW_SEEDS = [2, 3, 4, 5, 6]
PAIR_SEEDS = [2, 3]
# Defaults before tuning (historical campaign dev-001-baseline).
BASELINE = {"temp_start": 0.5, "temp_end": 0.01, "vnd_neighbours": 30, "destroy_weights": [1, 1, 1, 1, 0.5]}
FINAL_DESTROY = [1, 0, 1, 1, 0.5]          # random, worst, shaw, string, route
FINAL_REPAIR = [1, 1, 1, 1]                # greedy, regret2, regret3, blink
NEIGHBOURHOODS = ["relocate", "swap", "two_opt_star", "or_opt", "two_opt"]
SETS = ("confirmation", "temperature", "ablation")


def experiments():
    """(set, name, config overrides, seeds, description) in priority order."""
    plan = [("confirmation", "conf-final", {}, NEW_SEEDS, "frozen configuration (reference)"),
            ("confirmation", "conf-baseline", BASELINE, NEW_SEEDS, "historical baseline (dev-001 settings)")]
    for t in (0.25, 0.5, 1.0, 2.5, 4.0):
        name = f"temp-{t:g}".replace(".", "p")  # campaign IDs allow letters, digits, - and _ only
        plan.append(("temperature", name, {"temp_start": t, "temp_end": round(t / 75, 6)},
                     PAIR_SEEDS, f"start temperature {t:g} x mean arc, end = start/75"))
    for i, name in enumerate(["random", "worst", "shaw", "string", "route"]):
        if FINAL_DESTROY[i]:
            weights = list(FINAL_DESTROY)
            weights[i] = 0
            plan.append(("ablation", f"abl-no-{name}", {"destroy_weights": weights}, PAIR_SEEDS,
                         f"without {name} removal"))
    for i, name in enumerate(["greedy", "regret2", "regret3", "blink"]):
        weights = list(FINAL_REPAIR)
        weights[i] = 0
        plan.append(("ablation", f"abl-no-{name}", {"repair_weights": weights}, PAIR_SEEDS,
                     f"without {name} insertion"))
    for nb in NEIGHBOURHOODS:
        plan.append(("ablation", f"abl-no-{nb.replace('_', '')}",
                     {"neighbourhoods": [x for x in NEIGHBOURHOODS if x != nb]}, PAIR_SEEDS, f"VND without {nb}"))
    return plan


def log(out, message):
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
    print(line, flush=True)
    with (out / "progress.log").open("a") as handle:
        handle.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("run", "plan"))
    parser.add_argument("--only", nargs="*", help="run only these experiment names")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--instances", nargs="*", help="restrict instances (smoke tests only)")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out
    plan = [e for e in experiments() if not args.only or e[1] in args.only]
    if args.command == "plan":
        for group, name, config, seeds, text in plan:
            print(f"{group:12s} {name:18s} seeds {seeds}  {text}  {json.dumps(config)}")
        return 0
    out.mkdir(parents=True, exist_ok=True)

    # Freeze the notebook solver once (shared by every campaign) and validate all configs.
    from scripts.notebook_solver import load, notebook_sources
    solver_dir = out / "solver"
    alns, _ = load(notebook_sources(), build_dir=solver_dir)
    for _, name, config, _, _ in plan:
        alns.ALNSConfig.from_dict(config)
    alns.warmup()
    (out / f"plan-{datetime.now():%Y%m%d-%H%M%S}.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(), solver_version=alns.VERSION,
        solver_sha256=alns.solver.source_fingerprint(), budget="max(10, 0.1 x customers) s",
        split="development", workers=args.workers, baseline=BASELINE,
        experiments=[dict(set=g, name=n, config=c, seeds=s, description=t) for g, n, c, s, t in plan]), indent=2))
    log(out, f"START {len(plan)} campaigns, solver {alns.VERSION}, {args.workers} workers")

    contexts, queue = {}, []
    for group, name, config, seeds, text in plan:
        target = out / name
        if (target / "alns_report.md").is_file():
            log(out, f"{name}: already complete, skipped")
            continue
        if target.exists():
            aside = target.with_name(f"{name}.incomplete-{datetime.now():%Y%m%d-%H%M%S}")
            target.rename(aside)
            log(out, f"{name}: interrupted earlier, moved to {aside.name}")
        campaign_args = SimpleNamespace(
            split_file=SPLIT, split="development", instances=args.instances, families=None, classes=None,
            seeds=seeds, time_per_customer=0.1, min_time=10.0, config=json.dumps(config), config_file=None,
            variant=name, workers=args.workers, data_root=DATA_ROOT, output=target, solver_build=solver_dir)
        ctx = prepare_campaign(campaign_args)  # validates, warms the cache, writes the manifest
        ctx["name"], ctx["remaining"] = name, len(ctx["jobs"])
        contexts[name] = ctx
        rank = SETS.index(group)
        queue.extend((rank, -ctx["limits"][job[0]], name, job) for job in ctx["jobs"])
    queue.sort(key=lambda item: (item[0], item[1]))
    total = len(queue)
    log(out, f"QUEUED {total} attempts over {len(contexts)} campaigns "
             f"({sum(-item[1] for item in queue) / 3600:.1f} CPU-hours of time limits)")

    failures = finished = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(launch_job, contexts[name], job): name for _, _, name, job in queue}
        for future in as_completed(futures):
            name = futures[future]
            tag, code = future.result()
            finished += 1
            if code != 0:
                failures += 1
                log(out, f"attempt {name}/{tag} exited with {code}")
            ctx = contexts[name]
            ctx["remaining"] -= 1
            if ctx["remaining"] == 0:
                try:  # a reporting problem must never stop the remaining hours of runs
                    finalize_campaign(ctx)
                    overview = json.loads((ctx["out"] / "alns_overview.json").read_text())
                    gap = overview["mean_gap_equal_weight"]
                    log(out, f"{name}: DONE ({finished}/{total} attempts overall) feasible "
                             f"{overview['feasible_attempts']}/{overview['planned_attempts']}, budget ok "
                             f"{overview['budget_respected']}, mean gap "
                             f"{'n/a' if gap is None else format(gap, '.3f') + '%'}")
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    log(out, f"{name}: FINALIZE FAILED {type(exc).__name__}: {exc}")
    log(out, f"ALL DONE: {total} attempts, {failures} non-zero exits")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
