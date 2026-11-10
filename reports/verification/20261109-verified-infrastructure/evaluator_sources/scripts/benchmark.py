"""Independent static CVRPTW evaluation and durable campaigns. No routing search.

Public boundaries: Solver(instance, config, seed, time_limit) -> SolverResult;
run_campaign() enforces a wall-clock budget in an isolated spawned process.
Offline evaluation accepts saved customer-only routes through evaluate_solution().
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import queue
import subprocess
import sys
import time
import traceback
from typing import Protocol
import uuid

import numpy as np
import pandas as pd
import vrplib

from scripts.cvrptw_model import (
    CVRPTWInstance, check_cvrptw, load_cvrptw, require_cvrptw,
    reproducibility_metadata,
)

SCHEMA_VERSION = 1
SCORING = 'dimacs_truncate_1_decimal'


@dataclass
class SolverResult:
    routes: object
    departure_times: object = None
    status: str = 'completed'  # completed, timeout, no_solution, error
    claimed_cost: object = None
    trace: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class Solver(Protocol):
    def __call__(self, instance: CVRPTWInstance, config: dict,
                 seed: int, time_limit: float) -> SolverResult: ...


@dataclass(frozen=True)
class Thresholds:
    average_gap: float = 3.0
    investigate_gap: float = 7.0
    min_test_instances: int = 20
    min_seeds: int = 2

    def __post_init__(self):
        if not all(math.isfinite(v) and v >= 0 for v in (self.average_gap, self.investigate_gap)):
            raise ValueError('Gap thresholds must be finite and nonnegative')
        if self.min_test_instances < 20 or self.min_seeds < 2:
            raise ValueError('Final assessment requires at least 20 held-out instances and two seeds')


def plain(value):
    """Strict JSON conversion: unknown/nonfinite metrics stay null, never NaN/0."""
    if isinstance(value, dict) or hasattr(value, 'items'):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    if isinstance(value, np.ndarray): return plain(value.tolist())
    if isinstance(value, np.generic): return plain(value.item())
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, Path): return str(value)
    if value is None or isinstance(value, (str, int, float, bool)): return value
    return {'unserializable_type': type(value).__name__, 'repr': repr(value)}


def write_json(path, data):
    """Atomic, exclusive publication: never replace an existing artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        temporary.write_text(json.dumps(plain(data), indent=2, allow_nan=False) + '\n')
        os.link(temporary, path)  # Exclusive creation, even if another writer races.
    finally:
        temporary.unlink(missing_ok=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment(root):
    root = Path(root)
    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(root), *args], text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError): return None
    status = git('status', '--porcelain')
    source_hashes = {str(p.relative_to(root)): sha256(p) for p in sorted((root/'scripts').glob('*.py'))}
    memory = None
    try: memory = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    except (ValueError, OSError, AttributeError): pass
    return dict(commit=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                dirty=status != '' if status is not None else None, git_status=status,
                source_sha256=source_hashes, cpu=platform.processor() or platform.machine(),
                logical_cpus=os.cpu_count(), ram_bytes=memory,
                affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
                thread_environment={k: os.environ.get(k) for k in
                                    ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']})


def archive_evaluator(output, root, hashes):
    """Keep exact evaluator bytes as well as hashes, including uncommitted code."""
    for name, expected in hashes.items():
        source=Path(root)/name
        content=source.read_bytes()
        if hashlib.sha256(content).hexdigest()!=expected:
            raise RuntimeError(f'Evaluator changed during snapshot: {name}')
        target=Path(output)/'evaluator_sources'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream: stream.write(content)


def read_reference(instance, path, tolerance=1e-7):
    record = dict(status='missing_reference', kind='published BKS; optimality not proven',
                  path=str(path), sha256=None, supplied_cost=None, recomputed_cost=None, errors=[])
    try:
        record['sha256'] = sha256(path)
        ref = vrplib.read_solution(str(path))
        supplied = float(ref['cost'])
        if not math.isfinite(supplied) or supplied <= 0:
            raise ValueError('Reference cost must be finite and positive')
        audit = check_cvrptw(instance, [list(r) for r in ref['routes']], tolerance=tolerance)
        record.update(supplied_cost=supplied, recomputed_cost=audit['distance'])
        if not audit['feasible']: raise ValueError(audit['errors'])
        if abs(supplied-audit['distance']) > tolerance:
            raise ValueError(f'Reference cost mismatch: {supplied} vs {audit["distance"]}')
        record['status'] = 'verified'
    except FileNotFoundError as exc: record['errors'] = [str(exc)]
    except Exception as exc:
        record.update(status='invalid_reference', errors=[f'{type(exc).__name__}: {exc}'])
    return record


def evaluate_solution(instance, solution, reference, tolerance=1e-7):
    """Recompute all metrics from raw routes; never trust solver feasibility/cost."""
    require_cvrptw(instance)
    result = dict(feasible=False, status=solution.status, errors=[], cost=None, gap_percent=None,
                  gap_reason=None, vehicles_used=None, waiting_time=None, travel_duration=None,
                  service_duration=None, elapsed_duration=None, schedules=[], route_totals=[],
                  claimed_cost=solution.claimed_cost, cost_agrees=None, negative_gap_review=False,
                  tolerance=tolerance)
    if solution.status not in {'completed','timeout','no_solution','error'}:
        result.update(status='error', errors=['Unknown solver termination status'])
    elif solution.routes is not None:
        try:
            audit = check_cvrptw(instance, solution.routes, solution.departure_times, tolerance)
            totals = audit['route_totals']
            result.update(feasible=audit['feasible'], errors=audit['errors'], cost=audit['distance'],
                          vehicles_used=len(audit['active_routes']),
                          schedules=[t.to_dict('records') for t in audit['schedules']],
                          route_totals=totals.to_dict('records'))
            for output, column in [('waiting_time','waiting'),('travel_duration','driving'),
                                   ('service_duration','service'),('elapsed_duration','elapsed')]:
                result[output] = float(totals[column].sum()) if column in totals else None
            if not audit['feasible'] and solution.status == 'completed': result['status'] = 'infeasible'
        except Exception as exc:
            result.update(status='error', errors=[f'{type(exc).__name__}: {exc}'])
    else:
        if solution.status == 'completed': result['status'] = 'no_solution'
        result['errors'].append('No routes returned')
    if result['feasible'] and solution.claimed_cost is not None:
        try:
            claimed = float(solution.claimed_cost)
            result['cost_agrees'] = math.isfinite(claimed) and abs(claimed-result['cost']) <= tolerance
        except (TypeError, ValueError): result['cost_agrees'] = False
        if not result['cost_agrees']: result['errors'].append('Claimed cost disagrees with independent distance')
    # A raw verified-reference record is produced inside the campaign, never supplied by a solver.
    if not result['feasible']: result['gap_reason'] = 'infeasible_or_missing_solution'
    elif reference['status'] != 'verified': result['gap_reason'] = reference['status']
    else:
        base = reference['recomputed_cost']
        if not isinstance(base, (float,int)) or not math.isfinite(base) or base <= 0:
            result['gap_reason'] = 'invalid_reference_cost'
        else:
            result['gap_percent'] = 100 * (result['cost']-base)/base
            result['negative_gap_review'] = result['gap_percent'] < -tolerance
    return plain(result)


def _worker(solver, instance, config, seed, limit, output):
    started = time.perf_counter()
    try:
        instance = CVRPTWInstance(**instance)
        require_cvrptw(instance)
        result = solver(instance, config, seed, limit)
        if not isinstance(result, SolverResult): raise TypeError('Adapter must return SolverResult')
        output.put((result, time.perf_counter()-started, None))
    except Exception:
        output.put((SolverResult(None, status='error'), time.perf_counter()-started, traceback.format_exc()))


def run_solver(solver, instance, config, seed, time_limit):
    """Wall limit includes initialization and process startup; hard kill without incumbent if exceeded.

    Adapters returning a timeout incumbent before the deadline retain its score. A killed
    worker cannot supply an incumbent; cooperative stop/checkpoint adapters may be added later.
    """
    require_cvrptw(instance)
    if not math.isfinite(time_limit) or time_limit <= 0: raise ValueError('Positive finite time limit required')
    # MappingProxyType metadata isn't pickleable: reconstruct using plain owned arrays.
    payload = {k: getattr(instance, k) for k in instance.__dataclass_fields__}
    payload['benchmark_metadata'] = dict(instance.benchmark_metadata)
    context = mp.get_context('spawn'); output = context.Queue()
    process = context.Process(target=_worker, args=(solver, payload, config, seed, time_limit, output))
    started = time.perf_counter(); process.start()
    try:
        while True:
            remaining = time_limit-(time.perf_counter()-started)
            if remaining <= 0:
                solution, search_time, error = SolverResult(None, status='timeout'), None, 'Hard wall-clock deadline exceeded'
                break
            try:
                solution, search_time, error = output.get(timeout=min(.05, remaining))
                break
            except queue.Empty:
                if process.exitcode is not None:
                    solution, search_time, error = SolverResult(None, status='error'), None, f'Worker exited without a result (exit code {process.exitcode})'
                    break
        elapsed = time.perf_counter()-started
        overrun = elapsed > time_limit
        if overrun: solution.status = 'timeout'
        return solution, dict(search_seconds=search_time, execution_seconds=elapsed,
                              budget_respected=not overrun, error=error)
    finally:
        if process.is_alive(): process.terminate()
        process.join(timeout=2)
        if process.is_alive(): process.kill(); process.join()
        output.close()


def validate_plan(plan, root):
    """The declared Cartesian plan prevents hiding missing instances/seeds/attempts."""
    splits = plan['splits']
    if set(splits) != {'development','test'}: raise ValueError('Specify development and test splits')
    all_ids = splits['development'] + splits['test']
    if len(all_ids) != len(set(all_ids)): raise ValueError('Splits must be disjoint and contain unique IDs')
    if not all_ids: raise ValueError('Empty instance plan')
    for name in all_ids:
        p = (Path(root)/name).resolve()
        if Path(root).resolve() not in p.parents or p.suffix != '.vrp' or not p.is_file():
            raise ValueError(f'Unsupported/missing instance path: {name}')
    seeds = plan['seeds']
    if not seeds or any(isinstance(s,bool) or not isinstance(s,int) for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError('Seeds must be distinct integers')
    variants = plan['variants']
    if not variants or len({v['id'] for v in variants}) != len(variants): raise ValueError('Unique variants required')
    for variant in variants:
        if not variant['id'] or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in variant['id']):
            raise ValueError('Variant IDs may contain letters, digits, underscore and dash')
        if not variant.get('version'): raise ValueError('Explicit adapter/version label required')
        json.dumps(variant.get('config', {}), allow_nan=False)
    limits = plan['time_limits']
    for name in all_ids:
        limit = limits.get(name, limits.get('default'))
        if not isinstance(limit,(int,float)) or isinstance(limit,bool) or not math.isfinite(limit) or limit <= 0:
            raise ValueError(f'Positive finite time limit missing: {name}')
    if plan.get('mode') not in {'reference_fixture','external','solver'}: raise ValueError('Unknown campaign mode')
    Thresholds(**plan.get('thresholds', {}))
    return all_ids


def summarize(rows, plan):
    """Equal-weight instance means; failed attempts remain in all denominators."""
    thresholds = Thresholds(**plan.get('thresholds', {})); per_instance=[]; comparisons=[]
    for variant in plan['variants']:
        vid = variant['id']; means=[]; reasons=[]; investigations=[]
        planned = len(plan['splits']['test'])*len(plan['seeds'])
        selected = [r for r in rows if r['variant']==vid and r['split']=='test']
        for name in plan['splits']['test']:
            runs = [r for r in selected if r['instance_id']==name]
            gaps = [r['gap_percent'] for r in runs if r['gap_percent'] is not None and r['feasible']]
            times = [r['execution_seconds'] for r in runs if r['execution_seconds'] is not None]
            stats = dict(variant=vid, instance_id=name, attempted=len(runs), planned=len(plan['seeds']),
                         feasible=sum(r['feasible'] for r in runs), eligible_gaps=len(gaps),
                         gap_mean=float(np.mean(gaps)) if gaps else None,
                         gap_median=float(np.median(gaps)) if gaps else None,
                         gap_best=min(gaps) if gaps else None, gap_worst=max(gaps) if gaps else None,
                         gap_sd=float(np.std(gaps,ddof=1)) if len(gaps)>1 else None,
                         runtime_mean=float(np.mean(times)) if times else None,
                         runtime_median=float(np.median(times)) if times else None,
                         runtime_min=min(times) if times else None, runtime_max=max(times) if times else None,
                         runtime_sd=float(np.std(times,ddof=1)) if len(times)>1 else None,
                         vehicles_mean=float(np.mean([r['vehicles_used'] for r in runs if r['feasible']])) if gaps else None,
                         failures=sum(not r['feasible'] or r['status'] in {'error','no_solution'} for r in runs))
            per_instance.append(stats)
            if gaps: means.append(stats['gap_mean'])
            if gaps and max(gaps)>thresholds.investigate_gap:
                investigations.append(name)
                if not plan.get('investigations',{}).get(vid,{}).get(name): reasons.append(f'Investigation required: {name}')
        if len(plan['splits']['test'])<thresholds.min_test_instances: reasons.append('Too few distinct held-out instances')
        if len(plan['seeds'])<thresholds.min_seeds: reasons.append('Too few distinct seeds')
        expected={(n,s) for n in plan['splits']['test'] for s in plan['seeds']}
        actual=[(r['instance_id'],r['seed']) for r in selected]
        if set(actual)!=expected or len(actual)!=len(expected): reasons.append('Missing or duplicate planned attempts')
        if any(not r['feasible'] or r['gap_percent'] is None or r['status'] in {'error','no_solution'} or r['errors'] or r['cost_agrees'] is False for r in selected):
            reasons.append('Infeasible, failed, unverified or inconsistent attempt')
        if any(r['budget_respected'] is not True for r in selected): reasons.append('Unverified/exceeded runtime budget')
        if any(r.get('negative_gap_review') for r in selected): reasons.append('Negative gap requires independent review')
        mean=float(np.mean(means)) if means else None
        if mean is None or mean>thresholds.average_gap: reasons.append('Average gap exceeds target or unavailable')
        if plan['mode'] != 'solver': reasons.append('Infrastructure fixture/import; no executed solver quality claim')
        comparisons.append(dict(variant=vid,mean_gap=mean,instances_with_gaps=len(means),
                                planned_instances=len(plan['splits']['test']),attempts=len(selected),planned_attempts=planned,
                                feasibility_rate=sum(r['feasible'] for r in selected)/planned if planned else None,
                                investigations=investigations,assessment='NEEDS IMPROVEMENT' if reasons else 'PASS',reasons=reasons,
                                runtime_memory_targets='unresolved; no runtime/scalability PASS claimed'))
    return plain(per_instance), plain(comparisons)


def _write_csv(path, rows):
    stream=io.StringIO()
    if rows:
        keys=list(dict.fromkeys(k for row in rows for k in row))
        writer=csv.DictWriter(stream,fieldnames=keys); writer.writeheader()
        writer.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)
    path.write_text(stream.getvalue())


def run_campaign(plan, data_root, output, solvers=None, external=None):
    """Evaluate a frozen plan; fixtures deliberately cannot earn solver-quality PASS.

    external[(variant_id, instance_id, seed)] = SolverResult. Missing entries become
    recorded no_solution attempts. Imported timings are unknown and cannot earn PASS.
    solvers are top-level pickleable callables; they receive no .sol routes or costs.
    """
    plan=json.loads(json.dumps(plan,allow_nan=False))
    data_root=Path(data_root).resolve(); output=Path(output)
    names=validate_plan(plan,data_root)
    if plan['mode']=='solver' and (not solvers or any(v['id'] not in solvers for v in plan['variants'])):
        raise ValueError('Every planned variant requires an adapter')
    output.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    manifest=dict(schema_version=SCHEMA_VERSION,campaign_id=output.name,created_utc=datetime.now(timezone.utc).isoformat(),
                  plan=plan,environment=environment(repo),reproducibility=reproducibility_metadata(data_root,None),
                  reference_kind='published BKS; optimality not proven',inputs={},
                  note='Reference fixture replays are infrastructure tests, never optimization experiments.')
    for name in names:
        p=data_root/name
        manifest['inputs'][name]=dict(input_sha256=sha256(p),reference_sha256=sha256(p.with_suffix('.sol')) if p.with_suffix('.sol').exists() else None)
    archive_evaluator(output,repo,manifest['environment']['source_sha256'])
    write_json(output/'manifest.json',manifest); write_json(output/'split.json',plan['splits'])
    rows=[]
    for name in names:
        path=data_root/name; split='test' if name in plan['splits']['test'] else 'development'
        parse_started=time.perf_counter()
        try: instance=load_cvrptw(path); input_error=None
        except Exception as exc: instance=None; input_error=f'{type(exc).__name__}: {exc}'
        parsing=time.perf_counter()-parse_started
        ref_started=time.perf_counter()
        reference=read_reference(instance,path.with_suffix('.sol')) if instance else dict(status='invalid_instance',errors=[input_error])
        ref_seconds=time.perf_counter()-ref_started
        for variant in plan['variants']:
            for seed in plan['seeds']:
                started=time.perf_counter(); limit=plan['time_limits'].get(name,plan['time_limits'].get('default'))
                timing=dict(search_seconds=None,execution_seconds=None,budget_respected=None,error=None)
                if instance is None: solution=SolverResult(None,status='error')
                elif plan['mode']=='reference_fixture':
                    try:
                        raw=vrplib.read_solution(str(path.with_suffix('.sol')))
                        solution=SolverResult([list(r) for r in raw['routes']],claimed_cost=raw.get('cost'))
                    except Exception as exc:
                        solution=SolverResult(None,status='error'); timing['error']=str(exc)
                elif plan['mode']=='external': solution=(external or {}).get((variant['id'],name,seed),SolverResult(None,status='no_solution'))
                else:
                    try: solution,timing=run_solver(solvers[variant['id']],instance,variant.get('config',{}),seed,limit)
                    except Exception as exc:
                        solution=SolverResult(None,status='error'); timing['error']=f'{type(exc).__name__}: {exc}'
                validation_started=time.perf_counter()
                metrics=evaluate_solution(instance,solution,reference) if instance else dict(feasible=False,status='error',errors=[input_error],cost=None,gap_percent=None,
                    vehicles_used=None,cost_agrees=None,schedules=[],route_totals=[])
                validation_seconds=time.perf_counter()-validation_started
                if timing['error']: metrics['errors'].append(timing['error'])
                # Verify input/reference bytes were not changed by a run or a concurrent refresh.
                frozen=manifest['inputs'][name]
                if sha256(path)!=frozen['input_sha256'] or (sha256(path.with_suffix('.sol')) if path.with_suffix('.sol').exists() else None)!=frozen['reference_sha256']:
                    metrics.update(feasible=False,cost=None,gap_percent=None,status='error',errors=metrics['errors']+['Dataset/reference changed during campaign'])
                run_id=uuid.uuid4().hex
                directory=output/'runs'/variant['id']/Path(name).parent.name/Path(name).stem/str(seed)/run_id
                write_json(directory/'routes.json',dict(routes=solution.routes,departure_times=solution.departure_times))
                write_json(directory/'config.json',variant)
                write_json(directory/'schedule.json',dict(schedules=metrics.pop('schedules'),route_totals=metrics.pop('route_totals')))
                write_json(directory/'trace.json',solution.trace)
                write_json(directory/'log.json',dict(error=timing['error'],adapter_metadata=solution.metadata))
                row=dict(schema_version=SCHEMA_VERSION,campaign_id=output.name,run_id=run_id,utc=datetime.now(timezone.utc).isoformat(),
                         variant=variant['id'],version=variant['version'],instance_id=name,family=path.parent.name,split=split,seed=seed,
                         n=instance.n_customers if instance else None,K=instance.max_vehicles if instance else None,Q=instance.capacity if instance else None,
                         distance_policy=instance.distance_policy if instance else None,reference=reference,
                         input_sha256=frozen['input_sha256'],reference_sha256=frozen['reference_sha256'],
                         time_limit=limit,parsing_seconds=parsing,reference_validation_seconds=ref_seconds,
                         validation_seconds=validation_seconds,end_to_end_seconds=time.perf_counter()-started+parsing+ref_seconds,
                         artifact_dir=str(directory.relative_to(output)),**timing,**metrics)
                row['artifacts_sha256']={p.name:sha256(p) for p in directory.iterdir()}
                write_json(directory/'result.json',row)
                with (output/'runs.jsonl').open('a') as file: file.write(json.dumps(plain(row),allow_nan=False)+'\n'); file.flush(); os.fsync(file.fileno())
                rows.append(plain(row))
    per_instance,comparisons=summarize(rows,plan)
    _write_csv(output/'runs.csv',rows); _write_csv(output/'summary.csv',per_instance)
    _write_csv(output/'comparison.csv',comparisons); write_json(output/'comparison.json',comparisons)
    lines=['# Campaign comparison','',f"Mode: `{plan['mode']}`. Published BKS are not proven optima.",'',
           '| Variant | Mean gap % | Attempts | Feasible rate | Assessment |','| --- | ---: | ---: | ---: | --- |']
    for row in comparisons:
        lines.append(f"| {row['variant']} | {row['mean_gap']} | {row['attempts']}/{row['planned_attempts']} | {row['feasibility_rate']} | {row['assessment']} |")
    for row in comparisons: lines.extend(['',row['variant']+': '+'; '.join(row['reasons'])])
    (output/'comparison.md').write_text('\n'.join(lines)+'\n')
    write_comparison_artifacts(output, rows, per_instance, plan)
    return rows,comparisons



def write_comparison_artifacts(output, rows, per_instance, plan):
    """Descriptive paired bootstrap over INSTANCES, never over repeated seeds.

    Unadjusted percentile CIs are exploratory, with no significance claims. Only
    fully feasible paired instances enter; missing/excluded denominators are saved.
    """
    bootstrap_seed=2026; replicates=2000; rng=np.random.default_rng(bootstrap_seed)
    paired=[]; variants=[v['id'] for v in plan['variants']]
    for i,first in enumerate(variants):
        for second in variants[i+1:]:
            a={r['instance_id']:r for r in per_instance if r['variant']==first}
            b={r['instance_id']:r for r in per_instance if r['variant']==second}
            common=[n for n in plan['splits']['test'] if n in a and n in b and
                    all(t['eligible_gaps']==t['planned'] and t['attempted']==t['planned'] for t in (a[n],b[n]))]
            differences=np.array([a[n]['gap_mean']-b[n]['gap_mean'] for n in common])
            ci=None
            if len(differences)>=2:
                means=rng.choice(differences,size=(replicates,len(differences)),replace=True).mean(axis=1)
                ci=np.quantile(means,[.025,.975]).tolist()
            paired.append(dict(first=first,second=second,paired_instances=len(common),planned_instances=len(plan['splits']['test']),
                               mean_gap_difference=float(differences.mean()) if len(differences) else None,
                               bootstrap_percentile_ci95=ci,bootstrap_seed=bootstrap_seed,replicates=replicates,
                               note='Exploratory unadjusted intervals; no significance claim or multiple-testing conclusion'))
    write_json(output/'paired_comparisons.json',paired)
    family_rows=[]
    for variant in variants:
        for family in sorted({Path(n).parent.name for n in plan['splits']['test']}):
            subset=[r for r in per_instance if r['variant']==variant and Path(r['instance_id']).parent.name==family]
            eligible=[r['gap_mean'] for r in subset if r['gap_mean'] is not None]
            family_rows.append(dict(variant=variant,family=family,planned_instances=len(subset),instances_with_gaps=len(eligible),
                                    mean_gap=float(np.mean(eligible)) if eligible else None,
                                    attempted=sum(r['attempted'] for r in subset),feasible=sum(r['feasible'] for r in subset)))
    _write_csv(output/'family_summary.csv',family_rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for variant in variants:
        entries=[r for r in per_instance if r['variant']==variant and r['gap_mean'] is not None]
        if entries:
            axes[0].plot(range(len(entries)),[r['gap_mean'] for r in entries],'.',label=variant)
        timed=[r for r in rows if r['variant']==variant and r['execution_seconds'] is not None and r['split']=='test']
        if timed: axes[1].scatter([r['n'] for r in timed],[r['execution_seconds'] for r in timed],s=12,label=variant)
    thresholds=Thresholds(**plan.get('thresholds',{}))
    axes[0].axhline(thresholds.average_gap,color='green',linestyle='--',label='Average target (not per-instance requirement)')
    axes[0].axhline(thresholds.investigate_gap,color='red',linestyle=':',label='Investigation threshold')
    axes[0].set(xlabel='Instance ordinal (see summary.csv)',ylabel='Mean gap to published BKS (%)')
    axes[0].legend(fontsize=7)
    axes[1].set(xlabel='Customers',ylabel='Measured execution wall time (s)')
    if not any(r['execution_seconds'] is not None for r in rows):
        axes[1].text(.5,.5,'No solver runtime measured',ha='center',transform=axes[1].transAxes)
    fig.suptitle('Infrastructure replay/import — no solver quality evidence' if plan['mode']!='solver' else 'Executed adapter campaign')
    fig.tight_layout(); fig.savefig(output/'comparison.png',dpi=120); plt.close(fig)
