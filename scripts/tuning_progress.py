"""Show progress of the ALNS + VND tuning study (read-only, standard library only).

    python3 scripts/tuning_progress.py              # one snapshot
    python3 scripts/tuning_progress.py --watch 60   # refresh every 60 s (Ctrl+C to stop)

Counts finished attempts from the result.json files each attempt writes, per
campaign and overall, and estimates the time left from the throughput observed
so far (time limits of finished attempts per wall-clock second). It never
writes anything and does not interfere with the running study.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "results" / "alns-vnd" / "tuning-study"
SET_OF = {"conf": "confirmation", "temp": "temperature", "abl": "ablation"}


def runner_alive():
    try:
        return subprocess.run(["pgrep", "-f", "alns_tuning_study.py run"], capture_output=True).returncode == 0
    except OSError:
        return None


def started_at(study):
    log = study / "progress.log"
    if not log.is_file():
        return None
    starts = [line for line in log.read_text().splitlines() if " START " in line]
    return datetime.fromisoformat(starts[-1].split()[0]) if starts else None


def snapshot(study):
    campaigns = []
    for manifest in sorted(study.glob("*/manifest.json")):
        directory = manifest.parent
        if ".incomplete-" in directory.name:
            continue
        plan = json.loads(manifest.read_text())["plan"]
        names = sum(plan["splits"].values(), [])
        limits = plan["time_limits"]
        planned = {(n, s) for n in names for s in plan["seeds"]}
        done, failed = {}, 0
        for result in directory.glob("shards/*/runs/**/result.json"):
            try:
                row = json.loads(result.read_text())
            except (OSError, ValueError):
                continue  # being written right now
            done[(row["instance_id"], row["seed"])] = row
            failed += not (row.get("feasible") and row.get("budget_respected"))
        campaigns.append(dict(
            name=directory.name, set=SET_OF.get(directory.name.split("-")[0], "?"),
            planned=len(planned), done=len(done), failed=failed,
            complete=(directory / "alns_report.md").is_file(),
            limit_total=sum(limits[n] for n, _ in planned),
            limit_done=sum(limits[n] for n, _ in done),
            gaps=[r["gap_percent"] for r in done.values() if r.get("gap_percent") is not None]))
    order = {"confirmation": 0, "temperature": 1, "ablation": 2}
    campaigns.sort(key=lambda c: (order.get(c["set"], 9), c["name"]))  # execution order
    return campaigns


def fmt_duration(seconds):
    seconds = int(max(0, seconds))
    return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m" if seconds >= 3600 else f"{seconds // 60}m{seconds % 60:02d}s"


def show(study):
    campaigns = snapshot(study)
    if not campaigns:
        print(f"No tuning-study campaigns found under {study}")
        return
    print(f"Tuning study progress  {datetime.now():%Y-%m-%d %H:%M:%S}  ({study})")
    print(f"{'campaign':20s} {'set':12s} {'done':>9s} {'left':>5s} {'failed':>6s}  {'mean gap so far':>15s}  status")
    for c in campaigns:
        gap = f"{sum(c['gaps']) / len(c['gaps']):.3f} %" if c["gaps"] else "-"
        status = "complete" if c["complete"] else ("running" if c["done"] else "queued")
        print(f"{c['name']:20s} {c['set']:12s} {c['done']:4d}/{c['planned']:<4d} {c['planned'] - c['done']:5d} "
              f"{c['failed']:6d}  {gap:>15s}  {status}")
    planned = sum(c["planned"] for c in campaigns)
    done = sum(c["done"] for c in campaigns)
    failed = sum(c["failed"] for c in campaigns)
    limit_total = sum(c["limit_total"] for c in campaigns)
    limit_done = sum(c["limit_done"] for c in campaigns)
    print("-" * 86)
    print("Mean gap so far is provisional: the largest instances run first, so early values are high.")
    print(f"Attempts: {done}/{planned} done ({100 * done / planned:.1f} %), {planned - done} left, "
          f"{failed} infeasible/over budget")
    print(f"Work (by time limits): {100 * limit_done / limit_total:.1f} % done")
    start = started_at(study)
    alive = runner_alive()
    if start is not None:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        print(f"Elapsed since start: {fmt_duration(elapsed)}", end="")
        if limit_done > 0 and done < planned:
            rate = limit_done / elapsed  # budget-seconds finished per wall-clock second
            remaining = (limit_total - limit_done) / rate
            eta = datetime.now() + (datetime.fromtimestamp(time.time() + remaining) - datetime.now())
            print(f"   estimated time left: {fmt_duration(remaining)} (finish ~{eta:%H:%M} local time)")
        else:
            print()
    print("Runner process:", {True: "running", False: "NOT running", None: "unknown"}[alive])
    if alive is False and done < planned:
        print("  -> resume with: python scripts/alns_tuning_study.py run --workers 8 (completed campaigns are skipped)")
    if done == planned and all(c["complete"] for c in campaigns):
        print("All campaigns complete.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="refresh every SECONDS until Ctrl+C")
    parser.add_argument("--study", type=Path, default=STUDY)
    args = parser.parse_args()
    try:
        while True:
            if args.watch:
                print("\033[2J\033[H", end="")  # clear the terminal
            show(args.study)
            if not args.watch:
                return 0
            time.sleep(args.watch)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
