"""Regression tests: mathematical boundaries, hostile routes and native parsing."""
import copy
from dataclasses import FrozenInstanceError, replace
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import vrplib
from scripts.cvrptw_model import (
    CVRPTWInstance, check_cvrptw, check_temporal_equations, check_routing_equations,
    dimacs_tenths, normalize_service, load_cvrptw, verify_collection,
    CollectionVerificationError, reproducibility_metadata,
)
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/benchmarks/vrptw'


def tiny():
    return CVRPTWInstance('fixture',[0,1],2,2,[[0,1],[1,0]],[[0,10],[5,5]],[0,3])


class ModelTests(unittest.TestCase):
    def test_wait_start_close_completion_and_return(self):
        result=check_cvrptw(tiny(),[[1],[]])
        self.assertTrue(result['feasible']); row=result['schedules'][0].iloc[0]
        self.assertEqual((row.arrival,row.waiting,row.start,row.departure),(1,4,5,8))
        self.assertEqual(result['route_totals'].iloc[0].return_time,9)
        self.assertTrue(check_temporal_equations(tiny(),[[1],[]],result))

    def test_explicit_departures(self):
        for depart,valid in [(0,True),(4,True),(5,False),(-1,False),(11,False)]:
            with self.subTest(depart=depart): self.assertEqual(check_cvrptw(tiny(),[[1]],[depart])['feasible'],valid)
        for dep in [True,'4',float('inf')]:
            with self.assertRaises(ValueError): check_cvrptw(tiny(),[[1]],[dep])
        for dep in [4,[[4]],[],[0,0]]:
            with self.assertRaises(ValueError): check_cvrptw(tiny(),[[1]],dep)

    def test_depot_boundaries(self):
        self.assertTrue(check_cvrptw(replace(tiny(),time_windows=[[2,9],[5,5]]),[[1]],[2])['feasible'])
        self.assertFalse(check_cvrptw(replace(tiny(),time_windows=[[0,8],[5,5]]),[[1]])['feasible'])

    def test_route_rejections_have_no_score(self):
        for routes in [[],[[0,1]],[[2]],[[-1]],[[True]],[[1.0]],[[1],[1]],[[1],[1],[1]],[[[1]]],[None],[[1],None]]:
            with self.subTest(routes=routes):
                a=check_cvrptw(tiny(),routes); self.assertFalse(a['feasible']); self.assertIsNone(a['distance'])
        with self.assertRaises(ValueError): check_cvrptw(tiny(),np.array([[1]]))

    def test_zero_cases_and_capacity(self):
        inst=replace(tiny(),demands=[0,0],distances=[[0,0],[0,0]],travel_times=[[0,0],[0,0]],
                     time_windows=[[0,0],[0,0]],service_durations=[0,0])
        audit=check_cvrptw(inst,[[1]])
        self.assertTrue(audit['feasible']); self.assertEqual(audit['distance'],0)
        self.assertTrue(check_temporal_equations(inst,[[1]],audit))
        self.assertFalse(check_cvrptw(inst,[])['feasible'])
        self.assertTrue(check_cvrptw(replace(tiny(),capacity=1),[[1]])['feasible'])

    def test_asymmetric_separate_duration(self):
        inst=CVRPTWInstance('asym',[0,1,1],2,2,[[0,1,4],[2,0,1],[1,5,0]],[[0,10]]*3,[0,0,0])
        self.assertEqual(check_cvrptw(inst,[[1,2]])['distance'],3)
        self.assertFalse(check_cvrptw(inst,[[2,1]])['feasible'])
        self.assertTrue(check_cvrptw(replace(inst,travel_times=np.zeros((3,3))),[[2,1]])['feasible'])
        self.assertFalse(check_cvrptw(replace(inst,capacity=1),[[1,2]])['feasible'])
        self.assertTrue(check_cvrptw(replace(inst,capacity=1),[[1],[2]])['feasible'])

    def test_invalid_inputs(self):
        for change in [dict(demands=1),dict(demands=[0,float('nan')]),dict(demands=[1,1]),dict(max_vehicles=True),
                       dict(max_vehicles=1.5),dict(max_vehicles=0),dict(capacity=0),dict(capacity=float('inf')),
                       dict(capacity=.5),dict(distances=[[0]]),dict(travel_times=[[0,-1],[1,0]]),
                       dict(time_windows=None),dict(time_windows=[[0,10],[6,5]]),dict(service_durations=[1,3]),
                       dict(service_durations=[0,-1]),dict(coordinates=[[0,0]]),dict(original_ids=[1,1]),
                       dict(distance_tenths=[[0,20],[20,0]]),dict(distance_policy='unknown'),dict(original_ids=[{},{}]),
                       dict(distance_policy='dimacs_truncate_1_decimal')]:
            with self.subTest(change=change):
                self.assertTrue(replace(tiny(),**change).check_input())
                with self.assertRaises(ValueError): check_cvrptw(replace(tiny(),**change),[[1]])

    def test_type_guard_and_immutability(self):
        class CapacityOnly:
            def check_input(self): return []
        with self.assertRaises(TypeError): check_cvrptw(CapacityOnly(),[[1]])
        data=np.array([0.,1.]); inst=replace(tiny(),demands=data)
        data[1]=99; self.assertEqual(inst.demands[1],1)
        with self.assertRaises(ValueError): inst.demands[1]=99
        with self.assertRaises(FrozenInstanceError): inst.capacity=99
        with self.assertRaises(TypeError): inst.benchmark_metadata['new']=1
        self.assertEqual(inst.depot_index,0)

    def test_normalize_service(self):
        np.testing.assert_array_equal(normalize_service(3,3),[0,3,3])
        np.testing.assert_array_equal(normalize_service([0,2,4],3),[0,2,4])
        for service,N in [(-1,3),(float('nan'),3),([0,-1],2),([1,2],2),([0,float('inf')],2),([0],2),(1,0),(1,True)]:
            with self.subTest(service=service,N=N):
                with self.assertRaises(ValueError): normalize_service(service,N)

    def test_dimacs_exact_and_below_boundary(self):
        xy=np.random.default_rng(4).integers(-10000,10000,(32,2))
        ticks=dimacs_tenths(xy)
        for i in range(len(xy)):
            for j in range(len(xy)):
                squared=100*sum((int(a)-int(b))**2 for a,b in zip(xy[i],xy[j]))
                self.assertEqual(ticks[i,j],math.isqrt(squared))
        self.assertEqual(dimacs_tenths([[0,0],[3,4]])[0,1],50)
        self.assertEqual(dimacs_tenths([[0,0],[np.nextafter(1.,0.),0]])[0,1],9)
        for coords in [[],[1,2],[[0,0,float('nan')]],[[0,float('inf')]],[[1e20,0]]]:
            with self.assertRaises(ValueError): dimacs_tenths(coords)

    def test_temporal_corruption_and_mismatched_routes(self):
        audit=check_cvrptw(tiny(),[[1]])
        damaged=copy.deepcopy(audit); damaged['schedules'][0].loc[0,'arrival']+=.5
        with self.assertRaises(AssertionError): check_temporal_equations(tiny(),[[1]],damaged)
        self.assertFalse(check_temporal_equations(tiny(),[],audit))

    def test_tolerance_bounds(self):
        for tol in [-1,1e-5,float('nan')]:
            with self.assertRaises(ValueError): check_cvrptw(tiny(),[[1]],tolerance=tol)
        inst=replace(tiny(),time_windows=[[0,9-5e-8],[5,5]])
        self.assertTrue(check_cvrptw(inst,[[1]])['feasible'])
        self.assertFalse(check_cvrptw(inst,[[1]],tolerance=0)['feasible'])
        self.assertGreater(check_cvrptw(inst,[[1]])['route_totals'].iloc[0].depot_lateness,0)

    def test_subtour_zero_demand_and_time(self):
        n=3; K=2; inst=CVRPTWInstance('cycle',[0]*4,1,K,np.zeros((4,4)),[[0,0]]*4,[0]*4)
        x=np.zeros((K,4,4)); y=np.zeros((K,n)); z=np.array([1,0]); u=np.zeros((K,n))
        # Depot loop through 1 plus disconnected zero-time 2 -> 3 -> 2.
        x[0,0,1]=x[0,1,0]=x[0,2,3]=x[0,3,2]=1; y[0]=1; u[0]=[1,2,3]
        checks=check_routing_equations(inst,x,y,z,u)
        self.assertFalse(checks['mtz']); self.assertTrue(all(v for k,v in checks.items() if k!='mtz'))
        x[:]=0; x[0,0,1]=x[0,1,2]=x[0,2,3]=x[0,3,0]=1
        self.assertTrue(all(check_routing_equations(inst,x,y,z,u).values()))

    def test_native_load_and_independent_c101_cost(self):
        inst=load_cvrptw(DATA/'Solomon/C101.vrp'); ref=vrplib.read_solution(str(DATA/'Solomon/C101.sol'))
        self.assertEqual((inst.n_customers,inst.original_ids[0],inst.original_ids[1]),(100,1,2))
        self.assertEqual(inst.distance_policy,'dimacs_truncate_1_decimal')
        ticks=0
        for route in ref['routes']:
            path=[0]+list(route)+[0]
            for a,b in zip(path,path[1:]):
                squared=100*sum((int(x)-int(y))**2 for x,y in zip(inst.coordinates[a],inst.coordinates[b]))
                ticks+=math.isqrt(squared)
        self.assertEqual(ticks/10,827.3)
        self.assertEqual(check_cvrptw(inst,[list(r) for r in ref['routes']])['distance'],827.3)
        self.assertEqual(reproducibility_metadata(DATA,5)['seed'],5)

    def test_reordered_sections_are_rejected(self):
        text=(DATA/'Solomon/C101.vrp').read_text()
        with tempfile.TemporaryDirectory() as directory:
            for section in ['NODE_COORD_SECTION','DEMAND_SECTION','TIME_WINDOW_SECTION']:
                prefix,body=text.split(section,1); lines=body.splitlines()
                indices=[i for i,l in enumerate(lines) if l.strip() and l.split()[0].isdigit()][:2]
                lines[indices[0]],lines[indices[1]]=lines[indices[1]],lines[indices[0]]
                path=Path(directory)/'bad.vrp'; path.write_text(prefix+section+'\n'+'\n'.join(lines))
                with self.subTest(section=section):
                    with self.assertRaises(ValueError): load_cvrptw(path)


class CollectionTests(unittest.TestCase):
    def test_all_356_references(self):
        report=verify_collection(DATA,strict=True)
        self.assertEqual(report['checked'],356); self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['failures'],[])
        self.assertEqual(report['collection_sha256'],'73cc107742d4d73761df1b92f204c62010198c575d1f40af73afb0bbca1a0549')
        self.assertTrue((report['results'].status=='PASS').all())

    def test_all_failures_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            family=Path(directory)/'Solomon'; family.mkdir()
            for name in ['bad1','bad2']: (family/(name+'.vrp')).write_text('INVALID')
            with self.assertRaises(CollectionVerificationError) as caught: verify_collection(directory,strict=True)
            self.assertEqual(caught.exception.report['checked'],2)
            self.assertEqual(len(caught.exception.report['results']),2)
            self.assertEqual(caught.exception.report['status'],'FAIL')
            self.assertEqual(verify_collection(directory)['status'],'FAIL')
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(verify_collection(directory)['status'],'NOT RUN')

if __name__=='__main__': unittest.main()
