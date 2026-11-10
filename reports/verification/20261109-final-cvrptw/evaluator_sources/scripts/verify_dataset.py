"""Fresh, exhaustive reference verification with durable CSV/JSON evidence."""
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts.cvrptw_model import verify_collection, reproducibility_metadata, CollectionVerificationError
from scripts.benchmark import write_json, environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=ROOT/'data/benchmarks/vrptw')
    parser.add_argument('--output',type=Path,required=True,help='New evidence directory; refuses overwrite')
    args=parser.parse_args(); started=time.perf_counter()
    try: report=verify_collection(args.data_root,strict=True)
    except CollectionVerificationError as exc: report=exc.report
    args.output.mkdir(parents=True,exist_ok=False)
    report['results'].to_csv(args.output/'instances.csv',index=False)
    records=report.pop('results').to_dict('records')
    report.update(records=records,elapsed_seconds=time.perf_counter()-started,
                  reproducibility=reproducibility_metadata(args.data_root,None),environment=environment(ROOT),
                  evidence_type='supplied reference validation; no optimization executed')
    write_json(args.output/'verification.json',report)
    rows=['# Complete reference verification','',f"Status: **{report['status']}**. Checked {report['checked']} pairs.",'',
          'Published references are BKS, not proven optima. This run did not execute optimization.','',
          f"Collection SHA256: `{report['collection_sha256']}`",'', '| Family | Checked | Passed | Failed |','| --- | ---: | ---: | ---: |']
    for family in sorted({r['family'] for r in records}):
        subset=[r for r in records if r['family']==family]
        passed=sum(r['status']=='PASS' for r in subset)
        rows.append(f'| {family} | {len(subset)} | {passed} | {len(subset)-passed} |')
    rows.extend(['','Failures: '+ ('None.' if not report['failures'] else '\n\n'+'\n'.join(report['failures']))])
    (args.output/'README.md').write_text('\n'.join(rows)+'\n')
    print(f"{report['status']}: {report['checked']} pairs; {len(report['failures'])} failures; {args.output}")
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
