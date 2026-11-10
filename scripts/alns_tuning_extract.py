"""Extract per-run solver metadata and convergence traces from ALNS + VND campaigns.

The committed run ledgers (runs.jsonl) hold the evaluator's verdict for every
attempt (feasibility, independent cost, gap). The solver-side details used by
the tuning analysis in main.ipynb -- iterations, acceptance statistics, final
adaptive operator weights, temperatures and best-cost traces -- live in the raw
per-attempt files, which are not in Git. This script condenses them into small
CSV files that are committed and loaded by the notebook:

    <out>/run_metadata.csv   one row per attempt
    <out>/convergence.csv    best gap at 21 points of the time budget, per attempt
    <out>/provenance.json    sources, archive SHA-256 checks, extraction time
    <out>/routes/*.json      (optional, --routes) the routes of the median-gap seed of
                             selected instances, for route and time-window plots

Sources: a campaign directory with raw shards/, or its archived
results/alns-vnd/archives/<campaign>-shards.tar.gz, which is verified against the
SHA-256 recorded in <campaign>/shards.tar.gz.sha256 before use.

    python scripts/alns_tuning_extract.py --out results/alns-vnd/tuning-data/historical \\
        results/alns-vnd/dev-001-baseline ... results/alns-vnd/dev-007-noworst
    python scripts/alns_tuning_extract.py --out results/alns-vnd/run-data/test-001 \
        --routes Solomon/RC101.vrp --routes GH1000/RC1_10_3.vrp results/alns-vnd/test-001
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVES = ROOT / "results" / "alns-vnd" / "archives"
GRID = [i / 20 for i in range(21)]
DESTROY = ("random", "worst", "shaw", "string", "route")
REPAIR = ("greedy", "regret2", "regret3", "blink")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def attempt_files(campaign):
    """Yield (run_directory_key, {file_name: bytes}) for every attempt of a campaign."""
    shards = campaign / "shards"
    if shards.is_dir():
        for result in sorted(shards.glob("*/runs/**/result.json")):
            run = result.parent
            yield str(run.relative_to(campaign)), {p.name: p.read_bytes() for p in run.glob("*.json")}
        return
    archive = ARCHIVES / f"{campaign.name}-shards.tar.gz"
    files = {}
    with tarfile.open(archive) as tar:
        for member in tar:
            if member.isfile() and "/runs/" in member.name and member.name.endswith(
                    ("result.json", "log.json", "trace.json", "routes.json")):
                run, name = member.name.rsplit("/", 1)
                files.setdefault(run, {})[name] = tar.extractfile(member).read()
    yield from sorted(files.items())


def source_of(campaign):
    if (campaign / "shards").is_dir():
        return dict(kind="raw shards", path=str((campaign / "shards").relative_to(ROOT)))
    archive = ARCHIVES / f"{campaign.name}-shards.tar.gz"
    expected = (campaign / "shards.tar.gz.sha256").read_text().strip()
    actual = sha256(archive)
    if actual != expected:
        raise ValueError(f"{archive} SHA-256 {actual} does not match recorded {expected}")
    return dict(kind="archive", path=str(archive.relative_to(ROOT)), sha256=actual, verified=True)


def best_gap_curve(trace, limit, bks):
    """Best gap (%) at fractions of the time limit; None before the first solution."""
    points = sorted((t["seconds"] / limit, t["best_cost"]) for t in trace if t.get("best_cost") is not None)
    curve = []
    for fraction in GRID:
        known = [cost for t, cost in points if t <= fraction + 1e-12]
        curve.append(100 * (known[-1] - bks) / bks if known else None)
    return curve


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("campaigns", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--routes", action="append", default=[], metavar="INSTANCE_ID",
                        help="save the routes of this instance's median-gap seed (repeatable)")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    meta_rows, curve_rows, sources, kept = [], [], {}, {}
    for campaign in args.campaigns:
        campaign = campaign.resolve()
        sources[campaign.name] = source_of(campaign)
        count = 0
        for run_key, files in attempt_files(campaign):
            result = json.loads(files["result.json"])
            if result["instance_id"] in args.routes and result["feasible"] and "routes.json" in files:
                kept.setdefault((campaign.name, result["instance_id"]), []).append(
                    (result["gap_percent"], result["seed"], result, json.loads(files["routes.json"])))
            meta = json.loads(files["log.json"]).get("adapter_metadata", {}) if "log.json" in files else {}
            trace = json.loads(files["trace.json"]) if "trace.json" in files else []
            stats = meta.get("stats", {})
            iterations = meta.get("iterations")
            row = dict(campaign=campaign.name, instance_id=result["instance_id"], family=result["family"],
                       n=result["n"], seed=result["seed"], time_limit=result["time_limit"],
                       feasible=result["feasible"], budget_respected=result["budget_respected"],
                       gap_percent=result["gap_percent"], cost=result["cost"],
                       bks=result["reference"]["recomputed_cost"], vehicles=result["vehicles_used"],
                       version=meta.get("version"), iterations=iterations,
                       search_seconds=meta.get("search_seconds"),
                       iterations_per_second=(iterations / meta["search_seconds"]
                                              if iterations and meta.get("search_seconds") else None),
                       construction_seconds=meta.get("construction_seconds"),
                       time_to_best_seconds=meta.get("time_to_best_seconds"),
                       acceptance_rate=(stats["accepted"] / stats["iterations"] if stats.get("iterations") else None),
                       new_best_rate=(stats["new_best"] / stats["iterations"] if stats.get("iterations") else None),
                       vnd_moves_per_iteration=(stats["vnd_moves"] / stats["iterations"]
                                                if stats.get("iterations") and "vnd_moves" in stats else None),
                       temp_start=meta.get("config", {}).get("temp_start"),
                       temp_end=meta.get("config", {}).get("temp_end"),
                       vnd_neighbours=meta.get("config", {}).get("vnd_neighbours"),
                       mean_arc=meta.get("temperature", {}).get("mean_arc"),
                       initial_cost=meta.get("initial_cost"))
            for name in DESTROY:
                row[f"w_destroy_{name}"] = meta.get("final_destroy_weights", {}).get(name)
            for name in REPAIR:
                row[f"w_repair_{name}"] = meta.get("final_repair_weights", {}).get(name)
            meta_rows.append(row)
            if trace and result["feasible"] and row["bks"]:
                for fraction, gap in zip(GRID, best_gap_curve(trace, result["time_limit"], row["bks"])):
                    curve_rows.append(dict(campaign=campaign.name, instance_id=result["instance_id"],
                                           family=result["family"], seed=result["seed"],
                                           fraction=fraction, best_gap=gap))
            count += 1
        sources[campaign.name]["attempts"] = count
        print(f"{campaign.name}: {count} attempts from {sources[campaign.name]['kind']}", flush=True)
    for name, rows in (("run_metadata.csv", meta_rows), ("convergence.csv", curve_rows)):
        with (args.out / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for (campaign_name, instance_id), runs in sorted(kept.items()):
        runs.sort(key=lambda r: (r[0], r[1]))
        gap, seed, result, routes = runs[(len(runs) - 1) // 2]  # median-gap seed (lower median)
        target = args.out / "routes" / f"{instance_id.replace('/', '__').replace('.vrp', '')}__s{seed}.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(dict(
            campaign=campaign_name, instance_id=instance_id, seed=seed, run_id=result["run_id"],
            selection=f"median gap of {len(runs)} feasible seeds", gap_percent=gap, cost=result["cost"],
            bks=result["reference"]["recomputed_cost"], routes=routes["routes"],
            departure_times=routes.get("departure_times")), indent=1) + "\n")
        print(f"routes: {target.name} (gap {gap:.3f} %)")
    (args.out / "provenance.json").write_text(json.dumps(dict(
        extracted_utc=datetime.now(timezone.utc).isoformat(), script="scripts/alns_tuning_extract.py",
        note="Derived from raw per-attempt files; gaps and feasibility are the independent evaluator's values.",
        sources=sources), indent=2) + "\n")
    print(f"wrote {len(meta_rows)} runs, {len(curve_rows)} curve points to {args.out}")


if __name__ == "__main__":
    main()
