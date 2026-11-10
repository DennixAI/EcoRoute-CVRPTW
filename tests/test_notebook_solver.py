"""main.ipynb is the only source of the ALNS + VND solver: build, cache and reproducibility."""
import json
import tempfile
import unittest
from pathlib import Path

import nbformat

from scripts.notebook_solver import MAGIC, MODULES, NOTEBOOK, build, import_built, load, notebook_sources
from scripts.cvrptw_model import check_cvrptw
from tests.test_alns_vnd import random_instance


class NotebookSolverTests(unittest.TestCase):
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

    def test_build_rewrites_only_changed_files_and_reimports(self):
        sources = notebook_sources()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sorted(build(sources, tmp)), sorted(("__init__",) + MODULES))
            self.assertEqual(build(sources, tmp), [])  # unchanged text keeps files (and Numba's cache)
            package = import_built(tmp)
            self.assertEqual(Path(package.__file__).parent, Path(tmp, "alns_notebook"))
            edited = dict(sources, solver=sources["solver"].replace('VERSION = "', 'VERSION = "edited-', 1))
            self.assertEqual(build(edited, tmp), ["solver"])
            self.assertTrue(import_built(tmp).VERSION.startswith("edited-"), "re-import must not reuse stale modules")
        load()  # restore the shared build for other tests

    def test_deterministic_mode_is_reproducible(self):
        package, _ = load()
        instance = random_instance(30, 21)
        config = {"max_iterations": 400, "deterministic": True}
        first = package.solve(instance, config, 3, 120.0)
        second = package.solve(instance, config, 3, 120.0)
        self.assertTrue(first.metadata["reproducible"])
        self.assertEqual(first.routes, second.routes)
        self.assertEqual(first.claimed_cost, second.claimed_cost)
        self.assertTrue(check_cvrptw(instance, first.routes)["feasible"])
        with self.assertRaises(ValueError):
            package.ALNSConfig.from_dict({"deterministic": True})  # needs max_iterations


if __name__ == "__main__":
    unittest.main()
