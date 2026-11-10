"""Replay references or evaluate externally supplied solutions; never search routes.

A reference fixture is an infrastructure smoke test, not solver evidence. Algorithms
can later call scripts.benchmark.run_campaign(plan, root, output, solvers=...).
"""
import argparse
import json
from pathlib import Path
import sys
import vrplib

ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.benchmark import run_campaign, SolverResult
from scripts.cvrptw_model import FAMILY_COUNTS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=ROOT/'data/benchmarks/vrptw')
    parser.add_argument('--output',type=Path,required=True,help='New persistent campaign directory')
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--reference-fixture',action='store_true',help='20 diverse references x two seeds; zero search')
    group.add_argument('--manifest',type=Path,help='Frozen external campaign plan plus saved solution entries')
    args=parser.parse_args(); external={}
    if args.reference_fixture:
        # Illustrative plumbing coverage only, never a frozen final-test selection.
        families={f:sorted((args.data_root/f).glob('*.vrp')) for f in FAMILY_COUNTS}
        if any(not paths for paths in families.values()): parser.error('Missing benchmark families')
        names=[]
        # Interleave sizes; include C/R/RC distributions where present.
        for offset in range(4):
            for family,paths in families.items():
                choices=[]
                for prefix in ('C1','R1','RC1','C2'):
                    choices.append(next((p for p in paths if p.stem.startswith(prefix)),paths[0]))
                name=str(choices[offset].relative_to(args.data_root))
                if name not in names: names.append(name)
        test=names[:20]
        dev=next(str(p.relative_to(args.data_root)) for p in families['Solomon'] if str(p.relative_to(args.data_root)) not in test)
        plan=dict(mode='reference_fixture',splits=dict(development=[dev],test=test),seeds=[0,1],
                  variants=[dict(id='published-reference-replay',version='fixture-v1',config={})],
                  time_limits=dict(default=1.0),thresholds={},split_note='Infrastructure fixture only; not the final held-out split')
    else:
        manifest=json.loads(args.manifest.read_text()); plan=manifest['plan']
        if plan.get('mode')!='external': parser.error('Saved-solution manifests must use mode=external')
        for entry in manifest.get('solutions',[]):
            key=(entry['variant'],entry['instance_id'],entry['seed'])
            if key in external: parser.error(f'Duplicate saved solution {key}')
            if entry['variant'] not in {v['id'] for v in plan['variants']} or entry['instance_id'] not in sum(plan['splits'].values(),[]) or entry['seed'] not in plan['seeds']:
                parser.error(f'Solution outside declared plan: {key}')
            path=(args.manifest.parent/entry['path']).resolve()
            try:
                if path.suffix=='.sol':
                    data=vrplib.read_solution(str(path)); data['claimed_cost']=data.pop('cost',None)
                else: data=json.loads(path.read_text())
                external[key]=SolverResult(**{k:v for k,v in data.items() if k in SolverResult.__dataclass_fields__})
            except Exception as exc:
                external[key]=SolverResult(None,status='error',metadata={'source_error':str(exc)})
    rows,comparison=run_campaign(plan,args.data_root,args.output,external=external)
    passed=sum(r['feasible'] and r['gap_percent'] is not None for r in rows)
    print(f"Evaluated {len(rows)} attempts; {passed} feasible with verified gaps. Artifacts: {args.output}")
    print('Reference replays/imports cannot establish algorithm quality PASS.')
    return 0 if passed==len(rows) else 1

if __name__=='__main__': raise SystemExit(main())
