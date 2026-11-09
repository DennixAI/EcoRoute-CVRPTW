#!/usr/bin/env python3
"""Download the Solomon and Homberger CVRPTW benchmarks from PyVRP/Instances.

Place this file in the root of your project and run:
    python download_vrptw_benchmarks.py

Requires Python 3.9+; no third-party packages.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPOSITORY = "https://github.com/PyVRP/Instances"
ARCHIVE_URL = "https://codeload.github.com/PyVRP/Instances/zip/refs/heads/main"
DESTINATION = Path(__file__).resolve().parent / "data" / "benchmarks" / "vrptw"
EXPECTED_COUNTS = {
    "Solomon": 56,
    "GH200": 60,
    "GH400": 60,
    "GH600": 60,
    "GH800": 60,
    "GH1000": 60,
}


def download_archive() -> Path:
    """Download the repository ZIP to a temporary file with retries."""
    for attempt in range(1, 4):
        path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="pyvrp-instances-", suffix=".zip", delete=False) as temp:
                path = Path(temp.name)
                request = urllib.request.Request(
                    ARCHIVE_URL,
                    headers={"User-Agent": "CESI-EcoRoute-benchmark-downloader/1.0"},
                )
                with urllib.request.urlopen(request, timeout=90) as response:
                    shutil.copyfileobj(response, temp, length=1024 * 1024)
            if not zipfile.is_zipfile(path):
                raise ValueError("Downloaded content is not a valid ZIP archive")
            return path
        except (OSError, urllib.error.URLError, ValueError) as error:
            if path is not None:
                path.unlink(missing_ok=True)
            if attempt == 3:
                raise RuntimeError(f"Failed to download the GitHub archive: {error}") from error
            print(f"Download attempt {attempt} failed: {error}; retrying...")
            time.sleep(2 * attempt)
    raise AssertionError("Unreachable")


def dataset_target(archive_path: str) -> tuple[str, Path] | None:
    """Map GitHub ZIP member paths to our six local dataset folders."""
    parts = PurePosixPath(archive_path).parts
    if "VRPTW" not in parts:
        return None
    relative = parts[parts.index("VRPTW") + 1 :]
    if len(relative) == 2 and relative[0] in EXPECTED_COUNTS and relative[0] != "GH1000":
        family, filename = relative
    elif len(relative) == 1:
        family, filename = "GH1000", relative[0]  # GH1000 is at VRPTW/ root.
    else:
        return None
    if Path(filename).suffix.lower() not in (".vrp", ".sol"):
        return None
    if not filename or filename.startswith("."):
        return None
    return family, DESTINATION / family / filename


def main() -> None:
    print(f"Source: {REPOSITORY}")
    print("Downloading GitHub archive (contains other families that will be ignored)...")
    archive = download_archive()
    try:
        with zipfile.ZipFile(archive) as zf:
            selected: dict[str, zipfile.ZipInfo] = {}
            families: dict[str, dict[str, set[str]]] = {
                family: {".vrp": set(), ".sol": set()} for family in EXPECTED_COUNTS
            }
            for info in zf.infolist():
                if info.is_dir():
                    continue
                target = dataset_target(info.filename)
                if target is None:
                    continue
                family, destination = target
                key = str(destination)
                if key in selected:
                    raise ValueError(f"Duplicate archive entry: {key}")
                selected[key] = info
                families[family][destination.suffix].add(destination.stem)

            # Ensure the archive contains all 356 instances AND matching solutions.
            for family, expected in EXPECTED_COUNTS.items():
                problems, solutions = families[family][".vrp"], families[family][".sol"]
                if len(problems) != expected or problems != solutions:
                    raise RuntimeError(
                        f"Unexpected {family} contents: {len(problems)} .vrp, "
                        f"{len(solutions)} .sol; expected {expected} matching pairs."
                    )

            created = replaced = unchanged = 0
            for dest_string, info in sorted(selected.items()):
                destination = Path(dest_string)
                source_bytes = zf.read(info)  # Also validates this member's CRC.
                if destination.exists():
                    if destination.read_bytes() == source_bytes:
                        unchanged += 1
                        continue
                    replaced += 1
                else:
                    created += 1
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Atomic writes avoid leaving partial benchmark files on interruption.
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
                        temporary = Path(handle.name)
                        handle.write(source_bytes)
                    os.replace(temporary, destination)
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)

            # Keep upstream's documentation and licensing alongside the datasets.
            for member, filename in (
                ("VRPTW/README.md", "UPSTREAM_README.md"),
                ("LICENSE", "LICENSE"),
            ):
                matches = [x for x in zf.infolist() if x.filename.endswith("/" + member)]
                if len(matches) == 1:
                    DESTINATION.mkdir(parents=True, exist_ok=True)
                    (DESTINATION / filename).write_bytes(zf.read(matches[0]))

        sha256 = hashlib.sha256()
        with archive.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha256.update(chunk)
        manifest = {
            "source": REPOSITORY,
            "archive_url": ARCHIVE_URL,
            "downloaded_utc": datetime.now(timezone.utc).isoformat(),
            "archive_sha256": sha256.hexdigest(),
            "problem_type": "VRPTW (vehicle routing with time windows)",
            "families": EXPECTED_COUNTS,
            "total_instances": sum(EXPECTED_COUNTS.values()),
            "file_types": [".vrp", ".sol"],
        }
        (DESTINATION / "source_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nSaved to: {DESTINATION}")
        for family, count in EXPECTED_COUNTS.items():
            print(f"  {family:8s} {count:3d} problems + {count:3d} solutions")
        print(f"TOTAL: 356 instances, 356 solutions (712 files)")
        print(f"Created: {created}; updated: {replaced}; unchanged: {unchanged}")
    finally:
        archive.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
