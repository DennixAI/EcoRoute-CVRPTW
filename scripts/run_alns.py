"""ALNS + VND experiment CLI: frozen splits, parallel campaigns, reports.

Subcommands
-----------
split   Create the stratified development / test / reserve split (once).
run     Execute a campaign through the shared evaluator ``scripts.benchmark``:
        every attempt runs in an isolated worker with a hard wall-clock limit
        and is re-validated independently.  Attempts are spread over parallel
        shards (one shard = one instance x one seed); shard outputs are merged
        into a single campaign directory with the shared summary/comparison
        artifacts.
report  Build the ALNS-specific analysis (tables, convergence, scalability)
        from a merged campaign directory.

Examples
--------
    python scripts/run_alns.py split --output results/alns-vnd/split.json
    python scripts/run_alns.py run --split-file results/alns-vnd/split.json \\
        --split development --seeds 0 1 --time-per-customer 0.1 \\
        --output results/alns-vnd/dev-001
    python scripts/run_alns.py report results/alns-vnd/dev-001
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmark import (  # noqa: E402
    environment, plain, run_campaign, summarize, write_comparison_artifacts, write_json, _write_csv)
from scripts.cvrptw_model import FAMILY_COUNTS, reproducibility_metadata  # noqa: E402

DATA_ROOT = ROOT / "data/benchmarks/vrptw"
CLASSES = ("C1", "C2", "R1", "R2", "RC1", "RC2")


def instance_class(stem):
    """Solomon C101 -> C1, R205 -> R2, RC108 -> RC1; GH C1_2_1 -> C1, RC2_10_5 -> RC2."""
    match = re.match(r"^(RC|R|C)(\d)", stem)
    if not match:
        raise ValueError(f"Unrecognised instance name: {stem}")
    return match.group(1) + match.group(2)


# ------------------------------------------------------------------ split --
def cmd_split(args):
    """Stratified random split: per (size family, class) one test and one
    development instance; everything else stays in an untouched reserve that
    can serve as a fresh test set if the first evaluation forces changes."""
    rng = np.random.default_rng(args.seed)
    splits = dict(development=[], test=[], reserve=[])
    for family in FAMILY_COUNTS:
        names = sorted(p.stem for p in (args.data_root / family).glob("*.vrp"))
        for cls in CLASSES:
            group = [n for n in names if instance_class(n) == cls]
            order = rng.permutation(len(group))
            chosen = [f"{family}/{group[i]}.vrp" for i in order]
            splits["test"].append(chosen[0])
            splits["development"].append(chosen[1])
            splits["reserve"].extend(chosen[2:])
    record = dict(
        created_utc=datetime.now(timezone.utc).isoformat(), split_seed=args.seed,
        method="numpy default_rng(split_seed); within each (family, class) group of sorted stems, "
               "a random permutation assigns the first to test, the second to development, the rest to reserve",
        families=list(FAMILY_COUNTS), classes=list(CLASSES), counts={k: len(v) for k, v in splits.items()},
        note="Test instances must never be used for tuning. Reserve instances are untouched and "
             "may form a fresh held-out set if test results trigger algorithm changes.",
        **splits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, record)
    print(f"Split written to {args.output}: " + ", ".join(f"{k}={len(v)}" for k, v in splits.items()))
    return 0


# -------------------------------------------------------------------- run --
def time_limit_for(n, per_customer, minimum):
    return float(max(minimum, round(per_customer * n, 3)))


def cmd_shard(args):
    """Internal: run one shard plan with the shared campaign evaluator."""
    from scripts.notebook_solver import import_built
    plan = json.loads(args.plan.read_text())
    # The campaign froze the notebook solver into its own folder before any attempt.
    solve = import_built(plan["solver_build"]).solve
    solvers = {v["id"]: solve for v in plan["variants"]}
    rows, _ = run_campaign(plan, args.data_root, args.output, solvers=solvers)
    bad = [r for r in rows if not r["feasible"]]
    return 1 if bad else 0


def cmd_run(args):
    split = json.loads(args.split_file.read_text())
    if args.split not in ("development", "test", "reserve"):
        raise SystemExit("split must be development, test or reserve")
    names = list(split[args.split])
    if args.instances:
        unknown = sorted(set(args.instances) - set(names))
        if unknown:
            raise SystemExit(f"Instances outside the {args.split} split: {unknown}")
        names = [n for n in names if n in set(args.instances)]
    if args.families:
        names = [n for n in names if n.split("/")[0] in args.families]
    if args.classes:
        names = [n for n in names if instance_class(Path(n).stem) in args.classes]
    if not names:
        raise SystemExit("No instances selected")
    config = {}
    if args.config_file:
        config.update(json.loads(args.config_file.read_text()))
    if args.config:
        config.update(json.loads(args.config))
    config["clock"] = "process"  # the isolated worker charges start-up to the budget
    out = args.output
    if out.exists():
        raise SystemExit(f"{out} exists; campaigns are never overwritten")
    (out / "shards").mkdir(parents=True)
    # Freeze the solver written in main.ipynb into this campaign (code archived with the results).
    from scripts.notebook_solver import load, notebook_sources
    solver_pkg, _ = load(notebook_sources(), build_dir=out / "solver")
    ALNSConfig, VERSION, warmup = solver_pkg.ALNSConfig, solver_pkg.VERSION, solver_pkg.warmup
    source_fingerprint = solver_pkg.solver.source_fingerprint
    full_config = ALNSConfig.from_dict(config).to_dict()
    variant = dict(id=args.variant, version=VERSION, config=full_config)
    seeds = list(args.seeds)
    sizes = {n: 100 if n.startswith("Solomon") else int(n.split("/")[0][2:]) for n in names}
    limits = {n: time_limit_for(sizes[n], args.time_per_customer, args.min_time) for n in names}
    split_key = "test" if args.split in ("test", "reserve") else "development"
    full_plan = dict(mode="solver", splits={"development": [], "test": []}, seeds=seeds,
                     variants=[variant], time_limits=limits, thresholds={},
                     split_source=str(args.split_file), split_name=args.split,
                     budget_rule=f"time_limit = max({args.min_time}, {args.time_per_customer} * customers) seconds",
                     solver_build=str((out / "solver").resolve()))
    full_plan["splits"][split_key] = names
    # Compile / load the Numba cache once, outside any timed attempt.
    started = time.perf_counter()
    warmup()
    warm_seconds = time.perf_counter() - started
    manifest = dict(
        campaign_id=out.name, created_utc=datetime.now(timezone.utc).isoformat(), plan=full_plan,
        algorithm=dict(name="ALNS+VND", version=VERSION, source="main.ipynb, frozen into solver/",
                       source_sha256=source_fingerprint()),
        environment=environment(ROOT), reproducibility=reproducibility_metadata(args.data_root, None),
        split_file_sha256=__import__("hashlib").sha256(args.split_file.read_bytes()).hexdigest(),
        workers=args.workers, warmup_seconds=warm_seconds,
        note="Each attempt is a separate shard campaign evaluated by scripts.benchmark.run_campaign; "
             "this manifest describes the merged campaign. Concurrent workers share the machine: "
             "timings include that contention.")
    write_json(out / "manifest.json", manifest)
    write_json(out / "split.json", dict(source=str(args.split_file), split=args.split, instances=names))
    jobs = sorted(((n, s) for n in names for s in seeds), key=lambda j: -limits[j[0]])
    total = len(jobs)
    print(f"{total} attempts on {len(names)} instances x {len(seeds)} seeds, {args.workers} workers; "
          f"sequential time {sum(limits[n] for n, _ in jobs) / 3600:.2f} h", flush=True)

    def launch(job):
        name, seed = job
        tag = f"{name.replace('/', '__').replace('.vrp', '')}__s{seed}"
        plan = dict(full_plan, seeds=[seed], time_limits={name: limits[name]})
        plan["splits"] = {"development": [], "test": []}
        plan["splits"][split_key] = [name]
        plan_path = out / "shards" / f"{tag}.plan.json"
        plan_path.write_text(json.dumps(plan, indent=2))
        log = (out / "shards" / f"{tag}.log").open("w")
        code = subprocess.call([sys.executable, str(Path(__file__).resolve()), "shard", "--plan", str(plan_path),
                                "--output", str(out / "shards" / tag), "--data-root", str(args.data_root)],
                               stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT))
        log.close()
        return tag, code

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for tag, code in pool.map(launch, jobs):
            done += 1
            print(f"[{done}/{total}] {tag} exit={code}", flush=True)
    merge(out, full_plan)
    report(out)
    return 0


def merge(out, plan):
    rows = []
    for runs in sorted((out / "shards").glob("*/runs.jsonl")):
        shard = runs.parent.name
        for line in runs.read_text().splitlines():
            row = json.loads(line)
            row["shard"] = shard
            row["artifact_dir"] = f"shards/{shard}/{row['artifact_dir']}"
            rows.append(row)
    planned = {(n, s) for n in sum(plan["splits"].values(), []) for s in plan["seeds"]}
    present = {(r["instance_id"], r["seed"]) for r in rows}
    with (out / "runs.jsonl").open("x") as handle:
        for row in rows:
            handle.write(json.dumps(plain(row), allow_nan=False) + "\n")
    _write_csv(out / "runs.csv", rows)
    per_instance, comparisons = summarize(rows, plan)
    if plan["splits"]["test"]:
        _write_csv(out / "summary.csv", per_instance)
        _write_csv(out / "comparison.csv", comparisons)
        write_json(out / "comparison.json", dict(comparisons=comparisons,
                                                 missing_attempts=sorted(map(list, planned - present))))
        write_comparison_artifacts(out, rows, per_instance, plan)
    return rows


# ----------------------------------------------------------------- report --
def _load_rows(out):
    return [json.loads(line) for line in (out / "runs.jsonl").read_text().splitlines()]


def _p(values, q):
    return float(np.percentile(values, q)) if values else None


def iteration_throughput(metadata):
    """Time-weighted rate from paired solver iteration/search-time measurements.

    adapter_metadata.search_seconds measures the search loop through final route
    packaging; it excludes construction and worker startup. Do not substitute the
    benchmark row's broader search_seconds (the entire worker callable), the
    execution wall time, or the allocated budget. Missing/invalid pairs are
    excluded together, never converted to zero. Zero iterations is valid.
    """
    pairs = []
    for record in metadata:
        iterations = record.get("iterations")
        seconds = record.get("search_seconds")
        if (isinstance(iterations, (int, float)) and not isinstance(iterations, bool)
                and math.isfinite(iterations) and iterations >= 0
                and float(iterations).is_integer()
                and isinstance(seconds, (int, float)) and not isinstance(seconds, bool)
                and math.isfinite(seconds) and seconds > 0):
            pairs.append((iterations, seconds))
    return dict(
        iterations_per_search_second=(sum(i for i, _ in pairs) / sum(t for _, t in pairs)
                                      if pairs else None),
        throughput_runs=len(pairs),
    )


def plot_throughput(ax, per_instance):
    """Only positive measured rates can be displayed on the logarithmic axis."""
    points = [p for p in per_instance
              if p["iterations_per_search_second"] is not None
              and p["iterations_per_search_second"] > 0]
    ax.plot([p["n"] for p in points],
            [p["iterations_per_search_second"] for p in points], "o")
    ax.set(xlabel="customers", ylabel="ALNS iterations / measured search second",
           yscale="log", title="Throughput by size (excludes construction/startup)")


def report(out):
    """ALNS-specific tables and figures from a merged campaign."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out)
    rows = _load_rows(out)
    manifest = json.loads((out / "manifest.json").read_text())
    plan = manifest["plan"]
    names = sum(plan["splits"].values(), [])
    per = []
    for name in names:
        runs = [r for r in rows if r["instance_id"] == name]
        gaps = [r["gap_percent"] for r in runs if r["feasible"] and r["gap_percent"] is not None]
        meta = []
        for r in runs:
            log = out / r["artifact_dir"] / "log.json"
            meta.append(json.loads(log.read_text()).get("adapter_metadata", {}) if log.exists() else {})
        exe = [r["execution_seconds"] for r in runs if r["execution_seconds"] is not None]
        per.append(dict(
            **iteration_throughput(meta),
            instance=name, family=name.split("/")[0], cls=instance_class(Path(name).stem),
            n=runs[0]["n"] if runs else None, time_limit=runs[0]["time_limit"] if runs else None,
            attempts=len(runs), feasible=sum(r["feasible"] for r in runs),
            budget_ok=sum(r["budget_respected"] is True for r in runs),
            bks=runs[0]["reference"]["recomputed_cost"] if runs else None,
            best_cost=min((r["cost"] for r in runs if r["feasible"]), default=None),
            gap_mean=float(np.mean(gaps)) if gaps else None, gap_median=float(np.median(gaps)) if gaps else None,
            gap_best=min(gaps) if gaps else None, gap_worst=max(gaps) if gaps else None,
            gap_sd=float(np.std(gaps, ddof=1)) if len(gaps) > 1 else None,
            vehicles_mean=float(np.mean([r["vehicles_used"] for r in runs if r["feasible"]])) if gaps else None,
            bks_routes=None,
            exec_mean=float(np.mean(exe)) if exe else None,
            iterations_mean=float(np.mean([m.get("iterations", 0) for m in meta])) if meta else None,
            ttb_mean=float(np.mean([m["time_to_best_seconds"] for m in meta if m.get("time_to_best_seconds") is not None]))
            if meta else None,
            pre_call_mean=float(np.mean([m["pre_call_seconds"] for m in meta if m.get("pre_call_seconds") is not None]))
            if any(m.get("pre_call_seconds") is not None for m in meta) else None))
    _write_csv(out / "alns_instances.csv", per)
    all_gaps = [r["gap_percent"] for r in rows if r["feasible"] and r["gap_percent"] is not None]
    means = [p["gap_mean"] for p in per if p["gap_mean"] is not None]
    fam = []
    for family in FAMILY_COUNTS:
        sub = [p for p in per if p["family"] == family and p["gap_mean"] is not None]
        if sub:
            fam.append(dict(family=family, instances=len(sub), mean_gap=float(np.mean([p["gap_mean"] for p in sub])),
                            worst_gap=max(p["gap_worst"] for p in sub),
                            mean_sd=float(np.mean([p["gap_sd"] for p in sub if p["gap_sd"] is not None]))
                            if any(p["gap_sd"] is not None for p in sub) else None,
                            mean_iterations=float(np.mean([p["iterations_mean"] for p in sub])),
                            time_limit=sub[0]["time_limit"]))
    cls_rows = []
    for cls in CLASSES:
        sub = [p for p in per if p["cls"] == cls and p["gap_mean"] is not None]
        if sub:
            cls_rows.append(dict(cls=cls, instances=len(sub), mean_gap=float(np.mean([p["gap_mean"] for p in sub])),
                                 worst_gap=max(p["gap_worst"] for p in sub)))
    _write_csv(out / "alns_families.csv", fam)
    _write_csv(out / "alns_classes.csv", cls_rows)
    attempts = len(rows)
    planned = len(names) * len(plan["seeds"])
    feasible = sum(r["feasible"] for r in rows)
    overview = dict(
        campaign=out.name, split=plan.get("split_name"), instances=len(names), seeds=plan["seeds"],
        planned_attempts=planned, attempts=attempts, feasible_attempts=feasible,
        budget_respected=sum(r["budget_respected"] is True for r in rows),
        mean_gap_equal_weight=float(np.mean(means)) if means else None,
        median_instance_gap=float(np.median(means)) if means else None,
        p90_run_gap=_p(all_gaps, 90), worst_run_gap=max(all_gaps) if all_gaps else None,
        best_of_seeds_mean_gap=float(np.mean([p["gap_best"] for p in per if p["gap_best"] is not None])) if means else None,
        mean_within_instance_sd=float(np.mean([p["gap_sd"] for p in per if p["gap_sd"] is not None]))
        if any(p["gap_sd"] is not None for p in per) else None,
        instances_any_run_over_7=[p["instance"] for p in per if p["gap_worst"] is not None and p["gap_worst"] > 7],
        negative_gap_runs=sum(1 for g in all_gaps if g < -1e-7),
        budget_rule=plan.get("budget_rule"))
    # derived analysis files are regenerated on every report (raw runs never are)
    (out / "alns_overview.json").write_text(json.dumps(plain(overview), indent=2, allow_nan=False) + "\n")

    # --- figures -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    ax = axes[0]
    order = sorted(per, key=lambda p: (p["n"] or 0, p["instance"]))
    for i, p in enumerate(order):
        gaps = [r["gap_percent"] for r in rows if r["instance_id"] == p["instance"] and r["gap_percent"] is not None]
        if gaps:
            ax.plot([i] * len(gaps), gaps, ".", color="0.6", ms=3)
            ax.plot(i, np.mean(gaps), "o", color="C0", ms=5)
    ax.axhline(3, color="green", ls="--", lw=1, label="3% mean target")
    ax.axhline(7, color="red", ls=":", lw=1, label="7% investigation")
    ax.set(xlabel="instance (sorted by size)", ylabel="gap to published BKS (%)", title="Per-run (grey) and mean (blue) gaps")
    ax.legend(fontsize=7)
    ax = axes[1]
    sizes = sorted({p["n"] for p in per if p["gap_mean"] is not None})
    ax.boxplot([[p["gap_mean"] for p in per if p["n"] == s and p["gap_mean"] is not None] for s in sizes],
               labels=[str(s) for s in sizes])
    ax.set(xlabel="customers", ylabel="instance mean gap (%)", title="Scalability: gap by size")
    ax2 = axes[2]
    plot_throughput(ax2, per)
    fig.tight_layout()
    fig.savefig(out / "alns_gaps.png", dpi=120)
    plt.close(fig)

    # convergence: gap vs fraction of the time limit, averaged per family
    fig, ax = plt.subplots(figsize=(7, 4.5))
    grid = np.linspace(0, 1, 101)
    for family in FAMILY_COUNTS:
        curves = []
        for r in rows:
            if r["family"] != family or not r["feasible"]:
                continue
            trace_path = out / r["artifact_dir"] / "trace.json"
            if not trace_path.exists():
                continue
            trace = [t for t in json.loads(trace_path.read_text()) if t.get("best_cost") is not None]
            bks = r["reference"]["recomputed_cost"]
            if not trace or not bks:
                continue
            ts = np.array([t["seconds"] for t in trace]) / r["time_limit"]
            gs = 100 * (np.array([t["best_cost"] for t in trace]) - bks) / bks
            idx = np.searchsorted(ts, grid, side="right") - 1
            curve = np.where(idx >= 0, gs[np.clip(idx, 0, None)], np.nan)
            curves.append(curve)
        if curves:
            ax.plot(grid, np.nanmean(np.array(curves), axis=0), label=family)
    ax.set(xlabel="fraction of time limit", ylabel="mean best gap (%)", title="Convergence (mean over runs)",
           yscale="log")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "alns_convergence.png", dpi=120)
    plt.close(fig)

    lines = [f"# ALNS + VND campaign `{out.name}`", "",
             f"Split: **{plan.get('split_name')}**; {len(names)} instances x {len(plan['seeds'])} seeds; "
             f"budget: {plan.get('budget_rule')}. Gaps are to published BKS (not proven optima), "
             "recomputed by the independent evaluator.", "",
             "Throughput = total iterations / total measured solver search seconds over valid paired runs; "
             "construction and worker startup are excluded. Missing/nonpositive times are excluded, "
             "not replaced by the time budget. `throughput_runs` records the included run count; "
             "zero rates remain in CSV but are omitted from the log-scale throughput plot.", "",
             "| Metric | Value |", "| --- | ---: |"]
    for key in ("planned_attempts", "attempts", "feasible_attempts", "budget_respected", "mean_gap_equal_weight",
                "median_instance_gap", "p90_run_gap", "worst_run_gap", "best_of_seeds_mean_gap",
                "mean_within_instance_sd", "negative_gap_runs"):
        value = overview[key]
        lines.append(f"| {key.replace('_', ' ')} | {value:.3f} |" if isinstance(value, float) else f"| {key.replace('_', ' ')} | {value} |")
    lines += ["", f"Instances with any run above 7%: {overview['instances_any_run_over_7'] or 'none'}", "",
              "## By size family", "", "| Family | n | time limit (s) | mean gap % | worst run gap % | mean seed SD | iterations |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in fam:
        sd = f"{f['mean_sd']:.3f}" if f["mean_sd"] is not None else "-"
        lines.append(f"| {f['family']} | {f['instances']} | {f['time_limit']:.0f} | {f['mean_gap']:.3f} | "
                     f"{f['worst_gap']:.3f} | {sd} | {f['mean_iterations']:.0f} |")
    lines += ["", "## By instance class", "", "| Class | instances | mean gap % | worst run gap % |", "| --- | ---: | ---: | ---: |"]
    for c in cls_rows:
        lines.append(f"| {c['cls']} | {c['instances']} | {c['mean_gap']:.3f} | {c['worst_gap']:.3f} |")
    lines += ["", "## Per instance", "",
              "| Instance | n | BKS | best | mean gap % | best % | worst % | SD | feasible | vehicles | iterations | time-to-best s |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    fmt = lambda v, d=3: "-" if v is None else f"{v:.{d}f}"
    for p in order:
        lines.append(f"| {p['instance']} | {p['n']} | {fmt(p['bks'], 1)} | {fmt(p['best_cost'], 1)} | {fmt(p['gap_mean'])} | "
                     f"{fmt(p['gap_best'])} | {fmt(p['gap_worst'])} | {fmt(p['gap_sd'])} | {p['feasible']}/{p['attempts']} | "
                     f"{fmt(p['vehicles_mean'], 1)} | {fmt(p['iterations_mean'], 0)} | {fmt(p['ttb_mean'], 1)} |")
    lines += ["", "![gaps](alns_gaps.png)", "", "![convergence](alns_convergence.png)", ""]
    (out / "alns_report.md").write_text("\n".join(lines))
    print("\n".join(lines[:22]))
    return overview


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("split")
    p.add_argument("--seed", type=int, default=20261110)
    p.add_argument("--data-root", type=Path, default=DATA_ROOT)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--split-file", type=Path, required=True)
    p.add_argument("--split", required=True)
    p.add_argument("--instances", nargs="*")
    p.add_argument("--families", nargs="*")
    p.add_argument("--classes", nargs="*")
    p.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    p.add_argument("--time-per-customer", type=float, default=0.3)
    p.add_argument("--min-time", type=float, default=10.0)
    p.add_argument("--config", help="JSON object overriding ALNSConfig defaults")
    p.add_argument("--config-file", type=Path)
    p.add_argument("--variant", default="alns-vnd")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    p.add_argument("--data-root", type=Path, default=DATA_ROOT)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("shard")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--data-root", type=Path, default=DATA_ROOT)
    p = sub.add_parser("report")
    p.add_argument("campaign", type=Path)
    args = parser.parse_args()
    if args.command == "split":
        return cmd_split(args)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "shard":
        return cmd_shard(args)
    report(args.campaign)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
