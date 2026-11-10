"""CLI/path regressions; scripts are invoked from outside the repository."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.download_vrptw_benchmarks import DESTINATION, dataset_target
from tests.test_model import ROOT, DATA


class IntegrationTests(unittest.TestCase):
    def test_downloader_mapping_and_default_root(self):
        self.assertEqual(DESTINATION,DATA)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertEqual(dataset_target('Instances-main/VRPTW/C1_10_1.vrp',root),('GH1000',root/'GH1000/C1_10_1.vrp'))
            self.assertEqual(dataset_target('Instances-main/VRPTW/Solomon/C101.sol',root),('Solomon',root/'Solomon/C101.sol'))
            for name in ['Instances-main/CVRP/C101.vrp','Instances-main/VRPTW/README.md','Instances-main/VRPTW/other/C101.vrp']:
                self.assertIsNone(dataset_target(name,root))

    def test_cli_help_from_unrelated_directory(self):
        for script in ['run_modeling.py','verify_dataset.py','run_benchmarks.py','download_vrptw_benchmarks.py']:
            with self.subTest(script=script):
                run=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--help'],cwd='/private/tmp',capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertIn('usage:',run.stdout)

    def test_external_cli_records_invalid_solution_and_missing_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'bad.json').write_text(json.dumps({'routes':[[0,1]],'status':'completed'}))
            manifest={'plan':{'mode':'external','splits':{'development':[],'test':['Solomon/C101.vrp']},
                              'seeds':[0,1],'variants':[{'id':'bad-fixture','version':'v1','config':{}}],
                              'time_limits':{'default':1}},
                      'solutions':[{'variant':'bad-fixture','instance_id':'Solomon/C101.vrp','seed':0,'path':'bad.json'}]}
            (root/'manifest.json').write_text(json.dumps(manifest))
            run=subprocess.run([sys.executable,str(ROOT/'scripts/run_benchmarks.py'),'--manifest',str(root/'manifest.json'),
                                '--output',str(root/'results')],cwd='/private/tmp',capture_output=True,text=True)
            self.assertEqual(run.returncode,1,run.stderr)
            rows=[json.loads(l) for l in (root/'results/runs.jsonl').read_text().splitlines()]
            self.assertEqual([r['status'] for r in rows],['infeasible','no_solution'])
            self.assertTrue(all(r['cost'] is None and r['gap_percent'] is None for r in rows))
            self.assertEqual(json.loads((root/'results/comparison.json').read_text())[0]['assessment'],'NEEDS IMPROVEMENT')

if __name__=='__main__': unittest.main()
