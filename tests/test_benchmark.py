"""Infrastructure tests replay known routes and deliberately invalid fixtures only."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from scripts.benchmark import (SolverResult, Thresholds, evaluate_solution, read_reference,
    run_campaign, run_solver, summarize, validate_plan, write_json)
from scripts.cvrptw_model import load_cvrptw
from tests.test_model import tiny, DATA


# Execution/IPC test doubles: never construct, improve or select routes.
def replay_fixture(instance, config, seed, time_limit):
    return SolverResult(config['routes'],claimed_cost=2)


def failing_fixture(instance, config, seed, time_limit):
    raise RuntimeError('Deliberate test failure')


def crashed_fixture(instance, config, seed, time_limit):
    os._exit(17)  # Simulate a native extension crash, not a routing algorithm.


def slow_fixture(instance, config, seed, time_limit):
    time.sleep(2)
    return SolverResult(None,status='no_solution')


def timeout_incumbent_fixture(instance, config, seed, time_limit):
    return SolverResult(config['routes'],status='timeout')


def plan(mode='external'):
    return dict(mode=mode,splits={'development':[],'test':['Solomon/C101.vrp']},seeds=[0,1],
                variants=[dict(id='fixture',version='v1',config={})],time_limits={'default':3})


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.instance=load_cvrptw(DATA/'Solomon/C101.vrp')
        self.reference=read_reference(self.instance,DATA/'Solomon/C101.sol')

    def test_gap_is_recomputed_not_claimed(self):
        reference=dict(status='verified',recomputed_cost=1)
        metrics=evaluate_solution(tiny(),SolverResult([[1]],claimed_cost=-500),reference)
        self.assertEqual(metrics['cost'],2); self.assertEqual(metrics['gap_percent'],100)
        self.assertFalse(metrics['cost_agrees']); self.assertTrue(metrics['errors'])

    def test_invalid_routes_never_receive_gap(self):
        for routes in [[],[[1],[1]],[[0,1]],[[1.0]],[[5]],[[[1]]]]:
            with self.subTest(routes=routes):
                metrics=evaluate_solution(tiny(),SolverResult(routes),dict(status='verified',recomputed_cost=2))
                self.assertFalse(metrics['feasible']); self.assertIsNone(metrics['cost']); self.assertIsNone(metrics['gap_percent'])

    def test_waiting_duration_and_separate_timeout_status(self):
        metrics=evaluate_solution(tiny(),SolverResult([[1]],status='timeout'),dict(status='verified',recomputed_cost=2))
        self.assertEqual(metrics['status'],'timeout'); self.assertTrue(metrics['feasible'])
        self.assertEqual((metrics['waiting_time'],metrics['travel_duration'],metrics['service_duration'],metrics['elapsed_duration']),(4,2,3,9))

    def test_missing_and_bad_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ref.sol'
            self.assertEqual(read_reference(tiny(),path)['status'],'missing_reference')
            for contents in ['Route #1: 1\nCost 9\n','Route #1: 1\nCost nan\n','Route #1: 1\nCost 0\n','Route #1: 0 1\nCost 2\n']:
                path.write_text(contents)
                self.assertEqual(read_reference(tiny(),path)['status'],'invalid_reference')
        m=evaluate_solution(tiny(),SolverResult([[1]]),dict(status='missing_reference'))
        self.assertTrue(m['feasible']); self.assertIsNone(m['gap_percent'])

    def test_negative_gap_not_clamped(self):
        metrics=evaluate_solution(tiny(),SolverResult([[1]]),dict(status='verified',recomputed_cost=4))
        self.assertEqual(metrics['gap_percent'],-50); self.assertTrue(metrics['negative_gap_review'])

    def test_serialization_and_exclusive_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'x.json'; write_json(path,{'value':float('nan')})
            self.assertIsNone(json.loads(path.read_text())['value'])
            with self.assertRaises(FileExistsError): write_json(path,{'value':1})
            self.assertIsNone(json.loads(path.read_text())['value'])

    def test_plan_validation(self):
        validate_plan(plan(),DATA)
        for modify in [dict(seeds=[0,0]),dict(seeds=[True]),dict(splits={'development':['Solomon/C101.vrp'],'test':['Solomon/C101.vrp']}),
                       dict(splits={'development':[],'test':['../../README.md']}),dict(time_limits={'default':0}),
                       dict(variants=[dict(id='../escape',version='v1')])]:
            with self.subTest(modify=modify):
                with self.assertRaises(ValueError): validate_plan(dict(plan(),**modify),DATA)
        with self.assertRaises(ValueError): Thresholds(min_test_instances=1)

    def test_campaign_records_missing_attempts_and_preserves_previous_run(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'campaign'
            rows,summary=run_campaign(plan(),DATA,output)
            self.assertEqual(len(rows),2); self.assertTrue(all(r['status']=='no_solution' for r in rows))
            self.assertEqual(summary[0]['assessment'],'NEEDS IMPROVEMENT')
            self.assertEqual(summary[0]['feasibility_rate'],0)
            self.assertEqual(len((output/'runs.jsonl').read_text().splitlines()),2)
            self.assertTrue((output/'comparison.csv').is_file())
            self.assertEqual((output/'evaluator_sources/scripts/benchmark.py').read_bytes(),(DATA.parents[2]/'scripts/benchmark.py').read_bytes())
            with self.assertRaises(FileExistsError): run_campaign(plan(),DATA,output)

    def test_two_variants_and_two_seeds_reference_replay(self):
        p=plan('reference_fixture'); p['variants'].append(dict(id='second-fixture',version='v2',config={}))
        with tempfile.TemporaryDirectory() as directory:
            rows,summary=run_campaign(p,DATA,Path(directory)/'campaign')
            self.assertEqual(len(rows),4); self.assertTrue(all(r['feasible'] for r in rows))
            self.assertTrue(all(r['gap_percent']==0 for r in rows))
            self.assertTrue(all(r['assessment']=='NEEDS IMPROVEMENT' for r in summary))
            self.assertTrue(all(r['execution_seconds'] is None for r in rows))

    def test_enforced_execution_boundary(self):
        solution,timing=run_solver(replay_fixture,tiny(),{'routes':[[1]]},0,5)
        self.assertEqual(solution.status,'completed'); self.assertTrue(timing['budget_respected'])
        self.assertGreater(timing['search_seconds'],0); self.assertGreater(timing['execution_seconds'],timing['search_seconds'])
        solution,timing=run_solver(failing_fixture,tiny(),{},0,5)
        self.assertEqual(solution.status,'error'); self.assertIn('Deliberate test failure',timing['error'])
        solution,timing=run_solver(crashed_fixture,tiny(),{},0,5)
        self.assertEqual(solution.status,'error'); self.assertIn('exit code 17',timing['error'])
        solution,timing=run_solver(slow_fixture,tiny(),{},0,.05)
        self.assertEqual(solution.status,'timeout'); self.assertIsNone(solution.routes)
        self.assertFalse(timing['budget_respected'])
        solution,timing=run_solver(timeout_incumbent_fixture,tiny(),{'routes':[[1]]},0,5)
        self.assertEqual(solution.status,'timeout'); self.assertEqual(solution.routes,[[1]])
        self.assertTrue(timing['budget_respected'])

    def test_campaign_executes_replay_adapter_without_search(self):
        import vrplib
        routes=[list(r) for r in vrplib.read_solution(str(DATA/'Solomon/C101.sol'))['routes']]
        p=plan('solver'); p['variants'][0]['config']={'routes':routes}
        with tempfile.TemporaryDirectory() as directory:
            rows,comparison=run_campaign(p,DATA,Path(directory)/'campaign',solvers={'fixture':replay_fixture})
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r['feasible'] and r['gap_percent']==0 for r in rows))
            self.assertTrue(all(r['execution_seconds']>0 for r in rows))
            # Deliberately wrong claimed cost 2 must be independently detected.
            self.assertTrue(all(r['cost_agrees'] is False for r in rows))
            self.assertEqual(comparison[0]['assessment'],'NEEDS IMPROVEMENT')

    def test_quality_assessment_requires_every_planned_attempt(self):
        p=plan('solver'); p['splits']['test']=[f'I{i}' for i in range(20)]
        rows=[dict(variant='fixture',split='test',instance_id=name,seed=seed,feasible=True,gap_percent=1,
                   execution_seconds=1,vehicles_used=1,status='completed',budget_respected=True,errors=[],cost_agrees=True)
              for name in p['splits']['test'] for seed in p['seeds']]
        self.assertEqual(summarize(rows,p)[1][0]['assessment'],'PASS')
        self.assertEqual(summarize(rows[:-1],p)[1][0]['assessment'],'NEEDS IMPROVEMENT')
        rows[0]['gap_percent']=8
        self.assertEqual(summarize(rows,p)[1][0]['assessment'],'NEEDS IMPROVEMENT')
        p['investigations']={'fixture':{'I0':'Synthetic test outlier; retained, cause and remediation recorded'}}
        self.assertEqual(summarize(rows,p)[1][0]['assessment'],'PASS')

    def test_equal_weight_statistics_failure_and_investigation(self):
        p=plan('solver'); p['splits']['test']=['A','B']; p['seeds']=[0,1]
        rows=[]
        for name,gaps in [('A',[0,0]),('B',[0,8])]:
            for seed,gap in enumerate(gaps):
                rows.append(dict(variant='fixture',split='test',instance_id=name,seed=seed,feasible=True,
                                 gap_percent=gap,execution_seconds=1,vehicles_used=1,status='completed',
                                 budget_respected=True,errors=[],cost_agrees=True))
        stats,comparison=summarize(rows,p)
        self.assertEqual(comparison[0]['mean_gap'],2)
        self.assertEqual(stats[1]['gap_mean'],4); self.assertEqual(stats[1]['gap_worst'],8)
        self.assertAlmostEqual(stats[1]['gap_sd'],8/(2**.5))
        self.assertEqual(comparison[0]['investigations'],['B'])
        self.assertEqual(comparison[0]['assessment'],'NEEDS IMPROVEMENT')
        rows[0].update(feasible=False,gap_percent=None,status='error')
        self.assertLess(summarize(rows,p)[1][0]['feasibility_rate'],1)

if __name__=='__main__': unittest.main()
