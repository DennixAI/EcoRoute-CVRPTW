"""Build and import the ALNS + VND solver written in main.ipynb.

main.ipynb is the only source of the solver: its cells headed
``%%alns_source <module> <part>`` are the code.  This helper assembles those
cells into the package ``alns_notebook`` under ``outputs/alns_build/``
(generated, git-ignored, never edited by hand) and imports it.

Why a generated folder: Numba caches compiled machine code only for functions
that live in a real file.  Files are rewritten only when their text changes,
so the cache survives between runs and recompilation happens only after an
edit.  Isolated benchmark workers import the same generated package.

The notebook passes its in-memory cells to ``load``; tests and the benchmark
CLI read the saved notebook with ``notebook_sources``.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "main.ipynb"
BUILD_DIR = ROOT / "outputs" / "alns_build"
PACKAGE = "alns_notebook"
MODULES = ("_jit", "config", "kernels", "solver")
MAGIC = "%%alns_source"
INIT = ('"""ALNS + VND solver generated from main.ipynb -- do not edit; edit the notebook."""\n'
        "from .config import ALNSConfig\n"
        "from .solver import VERSION, solve, warmup\n")


def join_parts(parts):
    """Parts of one module, in part order, separated by two blank lines."""
    return "\n\n\n".join(p.strip("\n") for p in parts) + "\n"


def notebook_sources(notebook=NOTEBOOK):
    """{module: source} assembled from the saved notebook's solver cells."""
    cells = json.loads(Path(notebook).read_text())["cells"]
    parts = {name: {} for name in MODULES}
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        first, _, body = "".join(cell["source"]).partition("\n")
        if not first.startswith(MAGIC):
            continue
        fields = first.split()
        if len(fields) != 3 or fields[1] not in parts or not fields[2].isdigit():
            raise ValueError(f"Malformed solver cell header: {first!r}")
        if int(fields[2]) in parts[fields[1]]:
            raise ValueError(f"Duplicate solver cell {fields[1]} part {fields[2]}")
        parts[fields[1]][int(fields[2])] = body
    missing = [name for name in MODULES if not parts[name]]
    if missing:
        raise ValueError(f"{notebook} has no solver cells for {missing}")
    return {name: join_parts([parts[name][i] for i in sorted(parts[name])]) for name in MODULES}


def build(sources, build_dir=BUILD_DIR):
    """Write the package; only files whose text changed are rewritten.

    Returns the names of rewritten modules (empty when nothing changed)."""
    package_dir = Path(build_dir) / PACKAGE
    package_dir.mkdir(parents=True, exist_ok=True)
    files = {"__init__": INIT, **{name: sources[name] for name in MODULES}}
    changed = []
    for name, text in files.items():
        path = package_dir / f"{name}.py"
        if path.is_file() and path.read_text() == text:
            continue
        path.write_text(text)
        changed.append(name)
        # Never let Python reuse bytecode of the previous text.
        for stale in (package_dir / "__pycache__").glob(f"{name}.*.pyc"):
            stale.unlink()
    return changed


def import_built(build_dir=BUILD_DIR):
    """Import (or re-import) the generated package without rebuilding it."""
    for name in [k for k in sys.modules if k == PACKAGE or k.startswith(PACKAGE + ".")]:
        del sys.modules[name]  # a re-import must reflect the current files
    path = str(Path(build_dir))
    if path not in sys.path:
        sys.path.insert(0, path)
    importlib.invalidate_caches()
    return importlib.import_module(PACKAGE)


def load(sources=None, build_dir=BUILD_DIR):
    """Build from ``sources`` (default: the saved notebook) and import.

    Returns (package, rewritten_module_names)."""
    changed = build(sources if sources is not None else notebook_sources(), build_dir)
    existing = sys.modules.get(PACKAGE)
    if (not changed and existing is not None and getattr(existing, "__file__", None)
            and Path(existing.__file__).resolve().parent == (Path(build_dir) / PACKAGE).resolve()):
        return existing, changed  # same files already imported: keep the same objects
    return import_built(build_dir), changed
