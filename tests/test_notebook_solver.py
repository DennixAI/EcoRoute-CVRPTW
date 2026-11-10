"""main.ipynb is the authoritative ALNS + VND source; the .py copies must match it."""
import json
import os
import subprocess
import sys
import textwrap
import unittest

import nbformat

from scripts.sync_notebook_solver import MAGIC, MODULES, NOTEBOOK, differences, notebook_sources


class NotebookSolverTests(unittest.TestCase):
    def test_notebook_and_py_copies_are_identical(self):
        diffs = differences()
        self.assertEqual(diffs, {}, "Run `python scripts/sync_notebook_solver.py --write` after editing "
                                    "solver cells in main.ipynb:\n" + "\n".join(diffs.values()))

    def test_solver_cells_are_well_formed(self):
        notebook = nbformat.read(str(NOTEBOOK), as_version=4)
        nbformat.validate(notebook)
        parts = {name: [] for name in MODULES}
        for cell in notebook.cells:
            if cell.cell_type == "code" and cell.source.startswith(MAGIC):
                header, _, body = cell.source.partition("\n")
                _, module, part = header.split()
                parts[module].append(int(part))
                compile(body, f"main.ipynb:{module}:{part}", "exec")
                self.assertEqual(cell.outputs, [], "source notebook keeps outputs cleared")
        for module, numbers in parts.items():
            self.assertEqual(sorted(numbers), list(range(1, len(numbers) + 1)), module)

    def test_notebook_code_runs_as_its_own_package(self):
        """Mirror load_alns() fallback: exec notebook modules as package alns_notebook."""
        sources = json.dumps(notebook_sources())
        script = textwrap.dedent(f"""
            import json, sys, types
            sys.path.insert(0, {str(NOTEBOOK.parent)!r})
            texts = json.loads({sources!r})
            package = types.ModuleType("alns_notebook"); package.__path__ = []
            sys.modules["alns_notebook"] = package
            for m in {list(MODULES)!r}:
                module = types.ModuleType("alns_notebook." + m); module.__package__ = "alns_notebook"
                sys.modules[module.__name__] = module; setattr(package, m, module)
                exec(compile(texts[m], "<main.ipynb " + m + ">", "exec"), module.__dict__)
            package.solver.NOTEBOOK_SOURCE_SHA256 = {{"solver.py": "test"}}
            result = package.solver.warmup()
            assert result.status == "completed" and result.routes, result.status
            assert result.metadata["source_sha256"]["origin"] == "main.ipynb"
            assert "algorithms.alns_vnd" not in sys.modules
            print("ok")
        """)
        env = dict(os.environ, ECOROUTE_DISABLE_JIT="1")
        done = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True,
                              cwd=str(NOTEBOOK.parent), timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr[-3000:])
        self.assertIn("ok", done.stdout)


if __name__ == "__main__":
    unittest.main()
