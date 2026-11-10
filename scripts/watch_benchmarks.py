#!/usr/bin/env python3
"""Read-only live viewer for shared benchmark campaigns and parallel shards.

No solver imports or benchmark execution. Close the window or press Ctrl+C to stop.
"""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys


PROJECT = Path(__file__).resolve().parents[1]


def read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def discover_campaign():
    """Find the newest solver campaign across registered local worktrees."""
    roots = {PROJECT}
    try:
        listing = subprocess.run(
            ["git", "-C", str(PROJECT), "worktree", "list", "--porcelain"],
            check=True, capture_output=True, text=True,
        ).stdout
        roots.update(Path(line[9:]) for line in listing.splitlines()
                     if line.startswith("worktree "))
    except (OSError, subprocess.CalledProcessError):
        pass
    candidates = []
    for root in roots:
        for pattern in ("results/*/manifest.json", "results/*/*/manifest.json"):
            for path in root.glob(pattern):
                try:
                    manifest = read_json(path)
                    if manifest.get("plan", {}).get("mode") == "solver":
                        candidates.append((manifest.get("created_utc", ""), str(path.parent)))
                except (OSError, ValueError, AttributeError):
                    continue
    if not candidates:
        raise ValueError("No solver campaign found. Supply --campaign /absolute/path/to/campaign")
    return Path(max(candidates)[1])


def finite(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def key(record):
    return record.get("variant"), record.get("instance_id"), record.get("seed")


def eligible(record):
    """Display evaluator scores, excluding known invalid or unverified outputs."""
    return (record.get("feasible") is True
            and record.get("reference", {}).get("status") == "verified"
            and record.get("cost_agrees") is not False
            and finite(record.get("gap_percent")))


class ResultReader:
    """Cache unchanged files and retry incomplete JSON on the next refresh."""

    def __init__(self, root):
        self.root = root
        self.cache = {}

    def scan(self):
        paths = set(self.root.glob("runs/**/result.json"))
        paths.update(self.root.glob("shards/*/runs/**/result.json"))
        skipped = 0
        for path in list(self.cache):
            if path not in paths:
                del self.cache[path]
        for path in paths:
            try:
                stat = path.stat()
                stamp = stat.st_mtime_ns, stat.st_size
                if path not in self.cache or self.cache[path][0] != stamp:
                    record = read_json(path)
                    if not isinstance(record, dict) or not all(
                        field in record for field in ("variant", "instance_id", "seed", "run_id")
                    ):
                        raise ValueError("Not a complete attempt record")
                    self.cache[path] = stamp, record
            except (OSError, ValueError):
                skipped += 1
                self.cache.pop(path, None)
        # A merged campaign may contain copies of the same shard run.
        unique = {record["run_id"]: record for _, record in self.cache.values()}
        return sorted(unique.values(), key=lambda r: (r.get("utc", ""), r["run_id"])), skipped


def mean_by_instance(records):
    groups = defaultdict(list)
    for record in records:
        if eligible(record):
            groups[record["instance_id"]].append(record["gap_percent"])
    return (sum(sum(v) / len(v) for v in groups.values()) / len(groups)
            if groups else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path,
                        help="Campaign directory; default: newest solver campaign across Git worktrees")
    parser.add_argument("--interval", type=float, default=3.0, help="Poll interval in seconds (default: 3)")
    parser.add_argument("--save", type=Path, help="Optional PNG snapshot, refreshed when results change")
    args = parser.parse_args()
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("--interval must be finite and greater than zero")
    try:
        campaign = (args.campaign.expanduser().resolve() if args.campaign else discover_campaign())
        manifest = read_json(campaign / "manifest.json")
        plan = manifest["plan"]
        instances = list(dict.fromkeys(i for values in plan["splits"].values() for i in values))
        seeds = plan["seeds"]
        variants = [v["id"] for v in plan["variants"]]
        if not instances or not seeds or not variants:
            raise ValueError("Campaign plan has no instances, seeds or variants")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    if args.save:
        args.save = args.save.expanduser().resolve()
        if args.save == campaign or campaign in args.save.parents:
            parser.error("--save must be outside the observed campaign (results are read-only)")
        if args.save.suffix.lower() != ".png":
            parser.error("--save must end in .png")

    # Import only after arguments are validated. Matplotlib is already a project dependency.
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.animation import FuncAnimation
    from matplotlib.colors import Normalize

    if "agg" == matplotlib.get_backend().lower() or "inline" in matplotlib.get_backend().lower():
        parser.error("No interactive Matplotlib backend. On macOS try MPLBACKEND=MacOSX; "
                     "on Linux use a GUI-enabled Python with Tk/Qt.")

    expected = {(v, i, s) for v in variants for i in instances for s in seeds}
    rows = [(v, i) for v in variants for i in instances]
    target = plan.get("thresholds", {}).get("average_gap", 3.0)
    outlier = plan.get("thresholds", {}).get("investigate_gap", 7.0)
    try:
        started = datetime.fromisoformat(manifest.get("created_utc", "").replace("Z", "+00:00"))
        if started.tzinfo is None:
            started = None
    except (ValueError, TypeError):
        started = None
    reader = ResultReader(campaign)
    fig, axes = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
    fig.canvas.manager.set_window_title("EcoRoute live benchmarks")
    colorbar = [None]
    last_signature = [None]
    print("Watching:", campaign, flush=True)
    print("Read-only; partial statistics are not a final benchmark assessment. Close window to stop.", flush=True)

    def update(_):
        records, skipped = reader.scan()
        now = datetime.now(timezone.utc)
        signature = (tuple((r["run_id"], r.get("utc"), r.get("gap_percent"),
                            r.get("feasible"), r.get("status")) for r in records), skipped, int(now.timestamp() // 30))
        if signature == last_signature[0]:
            return
        last_signature[0] = signature
        planned = [r for r in records if key(r) in expected]
        # Retries are not silently substituted: show the latest per planned slot,
        # and explicitly count additional attempts in the title.
        latest = {key(r): r for r in planned}
        visible = list(latest.values())
        completed = len(latest)
        remaining = len(expected) - completed
        percent = 100.0 * completed / len(expected)
        finished_instances = sum(
            all((variant, instance, seed) in latest for variant in variants for seed in seeds)
            for instance in instances
        )
        eta = "waiting for completed runs"
        if remaining == 0:
            eta = "0m"
        elif started is not None and completed >= 2:
            elapsed = (now - started).total_seconds()
            if elapsed > 0:
                seconds = math.ceil(elapsed * remaining / completed)
                hours, rest = divmod(seconds, 3600)
                minutes, seconds = divmod(rest, 60)
                eta = f"~{hours}h {minutes:02d}m {seconds:02d}s"
        progress = (f"{completed}/{len(expected)} runs finished ({percent:.1f}%) | "
                    f"{remaining} LEFT | {finished_instances}/{len(instances)} instances fully run | "
                    f"ETA {eta}")
        scored = sum(eligible(r) for r in visible)
        feasible = sum(r.get("feasible") is True for r in visible)
        warnings = sum(r.get("budget_respected") is False or r.get("cost_agrees") is False
                       or r.get("negative_gap_review") is True or r.get("error") is not None
                       or r.get("status") != "completed" for r in visible)
        extra = len(planned) - completed
        outside = len(records) - len(planned)
        overall = mean_by_instance(visible)
        gap_text = "n/a" if overall is None else f"{overall:.2f}%"
        state = "PARTIAL" if completed < len(expected) else "ALL ATTEMPTS RECORDED"
        fig.suptitle(
            f"{campaign.name} | {state} | {progress}\n"
            f"feasible {feasible}/{completed} | scored {scored}/{completed} | mean gap {gap_text} | "
            "ETA uses campaign throughput; different run sizes can change it\n"
            f"{warnings} flagged attempts; {extra} retries (latest shown); {outside} outside plan; "
            f"{skipped} incomplete/unreadable files | refreshed {datetime.now():%H:%M:%S}\n"
            "Gaps to published BKS; feasible scored outputs only; no automatic PASS or optimality claim",
            fontsize=11,
        )
        if colorbar[0] is not None:
            colorbar[0].remove()
            colorbar[0] = None
        for ax in axes.flat:
            ax.clear()

        ax = axes[0, 0]
        for variant in variants:
            selected = [r for r in visible if r["variant"] == variant]
            prefix = []
            xs, ys = [], []
            for count, record in enumerate(selected, 1):
                prefix.append(record)
                value = mean_by_instance(prefix)
                if value is not None:
                    xs.append(count)
                    ys.append(value)
            ax.plot(xs, ys, marker=".", label=variant)
        ax.axhline(target, color="seagreen", linestyle="--", label=f"Target {target:g}%")
        ax.set(title="Running equal-weight mean of available instance means",
               xlabel="Finished planned runs per variant", ylabel="Gap to BKS (%)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)

        ax = axes[0, 1]
        groups = defaultdict(list)
        for r in visible:
            if eligible(r):
                groups[(r["variant"], r["instance_id"])].append(r["gap_percent"])
        for index, (variant, instance) in enumerate(rows):
            values = groups[(variant, instance)]
            if values:
                avg = sum(values) / len(values)
                ax.errorbar(index, avg, yerr=[[avg-min(values)], [max(values)-avg]],
                            fmt="o", markersize=3, color="crimson" if max(values)>outlier else "steelblue")
        ax.axhline(target, color="seagreen", linestyle="--")
        ax.axhline(outlier, color="crimson", linestyle=":")
        ax.set(title="Per-instance mean and min–max across completed seeds",
               ylabel="Gap to BKS (%)")
        labels = [Path(i).stem if len(variants)==1 else f"{v}/{Path(i).stem}" for v, i in rows]
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels(labels, rotation=90, fontsize=6)
        ax.grid(axis="y", alpha=0.2)

        ax = axes[1, 0]
        for variant in variants:
            selected = [r for r in visible if r["variant"] == variant
                        and finite(r.get("execution_seconds")) and finite(r.get("n"))]
            ax.scatter([r["n"] for r in selected], [r["execution_seconds"] for r in selected],
                       s=15, alpha=0.6, label=variant)
        ax.set(title="Measured worker execution time (includes startup)",
               xlabel="Customers", ylabel="Wall-clock seconds")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)

        ax = axes[1, 1]
        grid = np.full((len(rows), len(seeds)), np.nan)
        invalid = []
        for y, (variant, instance) in enumerate(rows):
            for x, seed in enumerate(seeds):
                record = latest.get((variant, instance, seed))
                if record is not None:
                    if eligible(record):
                        grid[y, x] = record["gap_percent"]
                    else:
                        invalid.append((x, y))
        cmap = plt.get_cmap("RdYlGn_r").copy()
        cmap.set_bad("#dedede")
        finite_values = grid[np.isfinite(grid)]
        low = min(0.0, float(finite_values.min())) if finite_values.size else 0.0
        high = max(float(outlier), float(finite_values.max())) if finite_values.size else float(outlier)
        plot = ax.imshow(np.ma.masked_invalid(grid), aspect="auto", interpolation="nearest",
                         cmap=cmap, norm=Normalize(vmin=low, vmax=high))
        if invalid:
            x, y = zip(*invalid)
            ax.scatter(x, y, marker="x", color="black", s=20)
        ax.set_xticks(range(len(seeds)))
        ax.set_xticklabels(seeds, fontsize=7)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels(labels, fontsize=max(3, min(7, 240 / len(rows))))
        ax.set(title="Seed coverage: gray=pending; ×=finished without eligible gap", xlabel="Seed")
        colorbar[0] = fig.colorbar(plot, ax=ax, label="Gap to BKS (%)", fraction=0.025)
        fig.canvas.draw_idle()
        print(f"{datetime.now():%H:%M:%S} {progress}; "
              f"feasible={feasible}; mean gap={gap_text}; flagged={warnings}", flush=True)
        if args.save:
            args.save.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.save.with_name(args.save.stem + ".tmp.png")
            fig.savefig(temporary, dpi=140)
            temporary.replace(args.save)

    animation = FuncAnimation(fig, update, interval=args.interval * 1000,
                              cache_frame_data=False)
    try:
        plt.show()
    except KeyboardInterrupt:
        plt.close(fig)
    # Keep animation alive for the lifetime of the GUI event loop.
    del animation
    return 0


if __name__ == "__main__":
    sys.exit(main())
