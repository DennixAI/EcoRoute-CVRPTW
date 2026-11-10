"""Keep the ALNS + VND solver in main.ipynb and algorithms/alns_vnd/*.py identical.

main.ipynb is the authoritative source of the solver.  Its solver cells start
with ``%%alns_source <module> <part>``; the parts of one module, joined in part
order, form that module.  The .py copies exist because Numba can only cache
compiled code for real files (so the notebook demo starts instantly) and because
isolated benchmark workers can only import code from files.

    python scripts/sync_notebook_solver.py           # check: exit 1 if they differ
    python scripts/sync_notebook_solver.py --write   # export notebook -> .py files

Comparison ignores blank lines and trailing whitespace (they do not change the
program); --write reproduces the notebook text exactly.
"""
import argparse
import difflib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "main.ipynb"
PACKAGE = ROOT / "algorithms" / "alns_vnd"
MODULES = ("_jit", "config", "kernels", "solver")
MAGIC = "%%alns_source"


def notebook_sources(notebook=NOTEBOOK):
    """{module: source text} assembled from the notebook's solver cells."""
    cells = json.loads(Path(notebook).read_text())["cells"]
    parts = {name: {} for name in MODULES}
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        text = "".join(cell["source"])
        first, _, body = text.partition("\n")
        if not first.startswith(MAGIC):
            continue
        fields = first.split()
        if len(fields) != 3 or fields[1] not in parts or not fields[2].isdigit():
            raise ValueError(f"Malformed solver cell header: {first!r}")
        index = int(fields[2])
        if index in parts[fields[1]]:
            raise ValueError(f"Duplicate solver cell {fields[1]} part {index}")
        parts[fields[1]][index] = body
    missing = [name for name in MODULES if not parts[name]]
    if missing:
        raise ValueError(f"Notebook has no solver cells for {missing}")
    return {name: join_parts([parts[name][i] for i in sorted(parts[name])]) for name in MODULES}


def join_parts(parts):
    return "\n\n\n".join(p.strip("\n") for p in parts) + "\n"


def normalized(text):
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def differences(notebook=NOTEBOOK, package=PACKAGE):
    """{module: unified diff} for modules whose code differs."""
    out = {}
    for name, text in notebook_sources(notebook).items():
        path = Path(package) / f"{name}.py"
        current = path.read_text() if path.exists() else ""
        if normalized(text) != normalized(current):
            out[name] = "\n".join(difflib.unified_diff(
                normalized(current), normalized(text), f"{name}.py", f"main.ipynb:{name}", lineterm=""))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="export notebook solver cells to the .py files")
    args = parser.parse_args()
    diffs = differences()
    if not diffs:
        print("main.ipynb solver cells and algorithms/alns_vnd/*.py are identical.")
        return 0
    if not args.write:
        for name, diff in diffs.items():
            print(diff)
        print(f"DIFFERENT: {sorted(diffs)}. Run with --write to export the notebook version.", file=sys.stderr)
        return 1
    for name, text in notebook_sources().items():
        if name in diffs:
            (PACKAGE / f"{name}.py").write_text(text)
            print(f"wrote algorithms/alns_vnd/{name}.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
