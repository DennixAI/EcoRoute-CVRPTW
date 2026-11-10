"""Static CVRPTW modeling checks. No route construction or optimization."""
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import hashlib
import importlib.metadata
import platform
import sys
import json
from types import MappingProxyType
from datetime import datetime, timezone
import numpy as np
import pandas as pd

FAMILY_COUNTS = {"Solomon": 56, "GH200": 60, "GH400": 60, "GH600": 60, "GH800": 60, "GH1000": 60}

@dataclass(frozen=True)
class CVRPTWInstance:
    name: str
    demands: object
    capacity: float
    max_vehicles: int
    distances: object
    time_windows: object
    service_durations: object
    coordinates: object = None
    original_ids: object = None
    distance_tenths: object = None
    travel_times: object = None
    source: str = "synthetic"
    distance_policy: str = "supplied"
    benchmark_metadata: object = field(default_factory=dict)

    @property
    def depot_index(self):
        """External depot labels are configurable through original_ids; internal depot is 0."""
        return 0

    def __post_init__(self):
        # Normalize containers, but never silently fix wrong shapes or depot service.
        for key in ("demands", "distances", "time_windows", "service_durations", "coordinates", "travel_times"):
            value = getattr(self, key)
            if value is not None:
                object.__setattr__(self, key, np.array(value, dtype=float, copy=True))
        if self.original_ids is not None: object.__setattr__(self, "original_ids", np.array(self.original_ids, copy=True))
        if self.distance_tenths is not None: object.__setattr__(self, "distance_tenths", np.array(self.distance_tenths, copy=True))
        if self.travel_times is None and self.distances is not None:
            object.__setattr__(self, "travel_times", self.distances.copy())  # Selected native convention t=d.

        # Copy caller-owned buffers, then guard accidental in-place solver mutation.
        for key in ("demands", "distances", "time_windows", "service_durations", "coordinates", "travel_times", "original_ids", "distance_tenths"):
            if getattr(self, key) is not None: getattr(self, key).setflags(write=False)
        metadata = json.loads(json.dumps(dict(self.benchmark_metadata), allow_nan=False))
        object.__setattr__(self, "benchmark_metadata", MappingProxyType(metadata))

    @property
    def n_customers(self):
        return self.demands.size - 1 if self.demands is not None and self.demands.ndim == 1 else 0

    def check_input(self):
        errors = []
        if self.demands is None or self.demands.ndim != 1 or self.demands.size < 2:
            return ["Demand vector must contain depot plus at least one customer"]
        N = self.demands.size
        for key, shape in (("distances", (N,N)), ("travel_times", (N,N)),
                           ("time_windows", (N,2)), ("service_durations", (N,))):
            v = getattr(self, key)
            if v is None or v.shape != shape or not np.all(np.isfinite(v)) or np.any(v < 0):
                errors.append(f"Invalid {key}: expected finite nonnegative {shape}")
        if not np.all(np.isfinite(self.demands)) or np.any(self.demands < 0) or self.demands[0] != 0:
            errors.append("Demands must be finite, nonnegative; depot demand must be zero")
        if isinstance(self.max_vehicles, (bool,np.bool_)) or not isinstance(self.max_vehicles,(int,np.integer)) or self.max_vehicles < 1:
            errors.append("K must be a positive integer")
        if isinstance(self.capacity,(bool,np.bool_)) or not isinstance(self.capacity,(int,float,np.integer,np.floating)) or not np.isfinite(self.capacity) or self.capacity <= 0:
            errors.append("Q must be finite and positive")
        elif np.any(self.demands > self.capacity): errors.append("Individual demand exceeds Q")
        if self.time_windows is not None and self.time_windows.shape == (N,2) and np.any(self.time_windows[:,0] > self.time_windows[:,1]):
            errors.append("Opening exceeds latest service start")
        if self.service_durations is not None and self.service_durations.shape == (N,) and self.service_durations[0] != 0:
            errors.append("Depot service must be zero under this model")
        if self.coordinates is not None and (self.coordinates.shape != (N,2) or not np.all(np.isfinite(self.coordinates))):
            errors.append("Optional coordinates must be finite (N,2)")
        if self.original_ids is not None:
            try:
                valid_ids = self.original_ids.shape == (N,) and len(set(self.original_ids.tolist())) == N
                valid_ids = valid_ids and all(isinstance(i, (str,int,np.integer)) and not isinstance(i,(bool,np.bool_)) for i in self.original_ids.tolist())
            except TypeError:
                valid_ids = False
            if not valid_ids: errors.append("Optional original IDs must be unique integer/string labels of length N")
        ticks = self.distance_tenths
        if ticks is not None:
            if ticks.shape != (N,N) or ticks.dtype.kind not in "iu" or np.any(ticks < 0):
                errors.append("Optional distance_tenths must be nonnegative integer (N,N)")
            elif self.distances is not None and self.distances.shape == (N,N) and not np.allclose(ticks/10,self.distances,rtol=0,atol=1e-12):
                errors.append("distance_tenths disagrees with distances")
        if self.distance_policy not in {"supplied", "raw", "nearest_integer", "ceil", "dimacs_truncate_1_decimal"}:
            errors.append("Unknown distance policy")
        if self.distance_policy == "dimacs_truncate_1_decimal" and ticks is None:
            errors.append("DIMACS policy requires an independently verifiable integer-tenths cache")
        return errors


def require_cvrptw(instance):
    """Reject legacy capacity-only containers at every shared solver/evaluator boundary."""
    if not isinstance(instance, CVRPTWInstance):
        raise TypeError("Expected authoritative CVRPTWInstance, including windows and service")
    errors = instance.check_input()
    if errors: raise ValueError(errors)
    return instance


def dimacs_tenths(xy):
    """Truncate, never round. Correct sqrt boundaries exactly for integer coordinates."""
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or not len(xy) or not np.all(np.isfinite(xy)):
        raise ValueError("Coordinates must be finite nonempty (N,2)")
    if np.max(np.abs(xy)) > 1e15:
        raise ValueError("Coordinates exceed safe int64 tenths range")
    delta = xy[:,None,:] - xy[None,:,:]
    if np.all(xy == np.floor(xy)) and np.max(np.abs(xy)) < 1e7:
        delta = delta.astype(np.int64)
        squared = 100 * np.sum(delta*delta,axis=2)
        ticks = np.sqrt(squared).astype(np.int64)
        ticks -= (ticks*ticks > squared)
        ticks += ((ticks+1)*(ticks+1) <= squared)
        return ticks
    # Other floating coordinate sources retain their numeric representation;
    # no epsilon that could promote a below-boundary distance is added.
    return np.floor(10*np.hypot(delta[...,0],delta[...,1])).astype(np.int64)

def normalize_service(value, N):
    if isinstance(N, (bool, np.bool_)) or not isinstance(N, (int, np.integer)) or N < 2:
        raise ValueError("N must include depot and at least one customer")
    service = np.asarray(value,dtype=float)
    if service.ndim == 0:
        if not np.isfinite(service) or service < 0: raise ValueError("Invalid scalar SERVICE_TIME")
        service = np.full(N,float(service)); service[0] = 0
    elif service.shape != (N,): raise ValueError("SERVICE_TIME must be scalar or length N")
    if not np.all(np.isfinite(service)) or np.any(service < 0) or service[0] != 0:
        raise ValueError("SERVICE_TIME must be finite nonnegative with zero depot service")
    return service.copy()

def load_cvrptw(path):
    import vrplib
    path = Path(path)
    raw = vrplib.read_instance(str(path),compute_edge_weights=False)
    if str(raw.get("type","")).upper() not in {"CVRPTW","VRPTW"}: raise ValueError("Expected selected VRPTW data")
    required = {"dimension","depot","vehicles","capacity","node_coord","demand","time_window","service_time"}
    if required - raw.keys(): raise ValueError(f"Missing required fields: {sorted(required-raw.keys())}")
    N = int(raw["dimension"])
    if N < 2 or N != raw["dimension"] or np.asarray(raw["depot"]).tolist() != [0]:
        raise ValueError("Expected depot array index 0 and DIMENSION >=2")
    # File IDs 1..N are a checked contract for this collection, not a general guess.
    if "NODE_COORD_SECTION" not in path.read_text(): raise ValueError("Missing coordinates section")
    ids=[]
    for line in path.read_text().split("NODE_COORD_SECTION",1)[1].splitlines():
        fields=line.split()
        if not fields: continue
        if not fields[0].isdigit(): break
        ids.append(int(fields[0]))
    if ids != list(range(1,N+1)): raise ValueError("Unexpected node labels/order: mapping required")
    # vrplib discards IDs in other sections too: reject reordered/missing labels.
    text = path.read_text()
    for section in ("DEMAND_SECTION", "TIME_WINDOW_SECTION", "SERVICE_TIME_SECTION"):
        if section not in text: continue
        labels = []
        for line in text.split(section, 1)[1].splitlines():
            fields = line.split()
            if not fields: continue
            if not fields[0].isdigit(): break
            labels.append(int(fields[0]))
        if labels != list(range(1, N+1)):
            raise ValueError(f"Unexpected node labels/order in {section}: mapping required")
    xy=np.asarray(raw["node_coord"],dtype=float)
    if xy.shape != (N,2) or not np.all(np.isfinite(xy)): raise ValueError("Invalid coordinates")
    if str(raw.get("edge_weight_type","")).upper() != "EUC_2D": raise ValueError("Unsupported edge type")
    K=float(raw["vehicles"])
    if not np.isfinite(K) or not K.is_integer(): raise ValueError("Noninteger VEHICLES")
    ticks=dimacs_tenths(xy)
    inst=CVRPTWInstance(name=str(raw.get("name",path.stem)),demands=raw["demand"],capacity=float(raw["capacity"]),
        max_vehicles=int(K),distances=ticks/10,coordinates=xy,original_ids=ids,
        time_windows=raw["time_window"],service_durations=normalize_service(raw["service_time"],N),
        distance_tenths=ticks,source=str(path),distance_policy="dimacs_truncate_1_decimal",
        benchmark_metadata={"input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(), "format":"PyVRP VRPLIB", "reference_kind":"published BKS, not proven optimum"})
    if inst.check_input(): raise ValueError(inst.check_input())
    return inst

def check_cvrptw(instance,routes,departure_times=None,tolerance=1e-7):
    """Audit supplied orders at supplied depot departures; never search for orders."""
    require_cvrptw(instance)
    if not np.isfinite(tolerance) or not 0 <= tolerance <= 1e-6: raise ValueError("Tolerance must be in [0,1e-6] benchmark units")
    if not isinstance(routes,(list,tuple)): raise ValueError("Routes must be sequences")
    errors=[]; active=[]; seen=[]
    for r in routes:
        if not isinstance(r,(list,tuple,np.ndarray)) or np.ndim(r)!=1:
            errors.append("Malformed route"); continue
        if len(r): active.append(list(r))
    if len(active)>instance.max_vehicles: errors.append("Fleet limit exceeded")
    if departure_times is None: departure_times=[instance.time_windows[0,0]]*len(active)
    if not isinstance(departure_times, (list, tuple, np.ndarray)) or np.ndim(departure_times) != 1:
        raise ValueError("Departures must be a finite numeric sequence")
    if len(departure_times)!=len(active): raise ValueError("One departure per nonempty route required")
    schedules=[]; totals=[]; distances=[]; total_ticks=0; N=instance.n_customers+1
    for k,(r,T) in enumerate(zip(active,departure_times),1):
        if any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) or not 1<=i<N for i in r):
            errors.append(f"Truck {k}: invalid customer IDs"); continue
        seen.extend(r)
        if isinstance(T, (bool, np.bool_)) or not isinstance(T, (int, float, np.integer, np.floating)):
            raise ValueError("Departure must be numeric, not boolean/string")
        T=float(T)
        if not np.isfinite(T): raise ValueError("Nonfinite departure")
        a0,H=instance.time_windows[0]
        if not a0-tolerance<=T<=H+tolerance: errors.append(f"Truck {k}: departure outside depot window")
        t=T; previous=0; rows=[]; driving=waiting=service=0.
        for i in r:
            travel=float(instance.travel_times[previous,i]); arrival=t+travel
            start=max(arrival,instance.time_windows[i,0]); wait=start-arrival
            t=start+instance.service_durations[i]; late=max(0.,start-instance.time_windows[i,1])
            if late>tolerance: errors.append(f"Truck {k}, customer {i}: late service start")
            rows.append(dict(customer=i,source_id=instance.original_ids[i] if instance.original_ids is not None else i,
                arrival=arrival,waiting=wait,start=start,departure=t,lateness=late))
            driving+=travel; waiting+=wait; service+=instance.service_durations[i]; previous=i
        t+=instance.travel_times[previous,0]; driving+=instance.travel_times[previous,0]
        if t>H+tolerance: errors.append(f"Truck {k}: late depot return")
        load=float(instance.demands[r].sum())
        if load>instance.capacity+tolerance: errors.append(f"Truck {k}: capacity exceeded")
        path=[0]+r+[0]
        if instance.distance_tenths is not None:
            route_ticks=sum(int(instance.distance_tenths[i,j]) for i,j in zip(path,path[1:]))
            total_ticks += route_ticks
            cost=route_ticks/10
        else: cost=sum(float(instance.distances[i,j]) for i,j in zip(path,path[1:]))
        distances.append(cost); schedules.append(pd.DataFrame(rows))
        totals.append(dict(truck=k,departure=T,return_time=t,elapsed=t-T,driving=driving,waiting=waiting,service=service,
            load=load,utilization=load/instance.capacity,distance=cost,depot_lateness=max(0.,t-H),
            capacity_excess=max(0.,load-instance.capacity),depot_early_departure=max(0.,a0-T),depot_departure_lateness=max(0.,T-H)))
    counts=Counter(seen)
    if set(seen)!=set(range(1,N)): errors.append("Missing customer coverage")
    if any(v!=1 for v in counts.values()): errors.append("Duplicate customers")
    # Undefined cost for malformed/invalid output; no deceptively favorable score.
    total_distance = total_ticks/10 if instance.distance_tenths is not None else sum(distances)
    if not np.isfinite(total_distance): errors.append("Nonfinite total distance")
    return dict(feasible=not errors,errors=errors,distance=total_distance if not errors else None,
        schedules=schedules,route_totals=pd.DataFrame(totals),tolerance=tolerance,
        active_routes=active,departure_times=list(departure_times))

def check_temporal_equations(instance,routes,audit):
    """Evaluate EVERY selected and inactive temporal arc for EVERY vehicle slot.

    Identical all-zero inactive slots are checked once, with multiplicity recorded.
    No sampled nodes. Vectorized one-vehicle matrices bound peak memory to O(N²).
    """
    require_cvrptw(instance)
    if not audit["feasible"]: return False
    try:
        fresh = check_cvrptw(instance, routes, audit["departure_times"], audit["tolerance"])
    except ValueError:
        return False
    if not fresh["feasible"]: return False
    if fresh["active_routes"] != audit["active_routes"]:
        raise AssertionError("Audit belongs to different routes")
    def ensure(condition):
        if not condition: raise AssertionError("Temporal equation residual or domain violation")
    N=instance.n_customers+1; K=instance.max_vehicles
    H=instance.time_windows[0,1]; tol=audit["tolerance"]; travel=instance.travel_times
    active=[r for r in routes if len(r)]; records=audit["route_totals"].to_dict("records")
    slots=len(active)+(len(active)<K)
    checked=0
    for k in range(slots):
        z=int(k<len(active)); y=np.zeros(N); A=np.zeros(N); S=np.zeros(N); D=np.zeros(N)
        x=np.zeros((N,N),dtype=bool); T=R=0.
        if z:
            r=active[k]; y[r]=1; T=records[k]["departure"]; R=records[k]["return_time"]
            for row in audit["schedules"][k].itertuples(): A[row.customer]=row.arrival; S[row.customer]=row.start; D[row.customer]=row.departure
            path=[0]+r+[0]; x[path[:-1],path[1:]]=True
        ensure(np.all(y<=z))
        for a in (A,S,D): ensure(np.all(a>=-tol) and np.all(a<=H*y+tol))
        ensure(np.all(S[1:]>=A[1:]-tol))
        ensure(np.all(S[1:]>=instance.time_windows[1:,0]*y[1:]-tol))
        ensure(np.all(S[1:]<=instance.time_windows[1:,1]*y[1:]+tol))
        ensure(np.allclose(D[1:],S[1:]+instance.service_durations[1:]*y[1:],rtol=0,atol=tol))
        ensure(instance.time_windows[0,0]*z-tol<=T<=R+tol and R<=H*z+tol)
        origin=D.copy(); origin[0]=T
        target=A.copy(); target[0]=R
        residual=target[None,:]-origin[:,None]-travel
        bound=(H+travel)*(~x)
        mask=~np.eye(N,dtype=bool)
        ensure(np.all(np.abs(residual[mask])<=bound[mask]+tol))
        checked+=N*(N-1)*(1 if z else K-len(active))
    ensure(checked==K*N*(N-1))
    return True

class CollectionVerificationError(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__(f"Collection verification failed: {report['failures']}")


def verify_collection(root, strict=False):
    """Audit every available pair, retain ALL failures; strict raises after audit."""
    import vrplib
    root=Path(root); missing=[]; paths=[]
    for family,count in FAMILY_COUNTS.items():
        vrps=sorted((root/family).glob("*.vrp")); sols=list((root/family).glob("*.sol"))
        if len(vrps)!=count or {p.stem for p in vrps}!={p.stem for p in sols}:
            missing.append(f"{family}: expected {count} matched pairs, found {len(vrps)} inputs/{len(sols)} solutions")
        paths.extend((family,p) for p in vrps)
    records=[]; digest=hashlib.sha256(); failures=list(missing)
    for family,path in paths:
        sol=path.with_suffix('.sol')
        record=dict(family=family,instance=path.stem,feasible=False,status="FAIL",error=None)
        try:
            record.update(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                reference_sha256=hashlib.sha256(sol.read_bytes()).hexdigest())
            digest.update(f"{family}/{path.name}:{record['input_sha256']}:{record['reference_sha256']}\n".encode())
            inst=load_cvrptw(path); ref=vrplib.read_solution(str(sol))
            audit=check_cvrptw(inst,[list(r) for r in ref['routes']])
            supplied=float(ref['cost'])
            if not np.isfinite(supplied) or supplied <= 0: raise ValueError("Reference cost must be finite and positive")
            record.update(n=inst.n_customers,K=inst.max_vehicles,Q=inst.capacity,
                reference_routes=len(audit['active_routes']),distance=audit['distance'],supplied_cost=supplied,
                feasible=audit['feasible'])
            if not audit['feasible']: raise ValueError(audit['errors'])
            if abs(audit['distance']-supplied)>1e-7: raise ValueError(f"Cost mismatch {audit['distance']} vs {supplied}")
            record['status']='PASS'
        except Exception as exc:
            record['error']=f"{type(exc).__name__}: {exc}"
            failures.append(f"{family}/{path.name}: {record['error']}")
        records.append(record)
    invalid = any(r['status'] != 'PASS' for r in records)
    status = 'FAIL' if invalid or (strict and missing) else ('NOT RUN' if missing else 'PASS')
    report=dict(status=status,checked=len(records),results=pd.DataFrame(records), reason='; '.join(missing),
        failures=failures,collection_sha256=digest.hexdigest())
    if strict and failures: raise CollectionVerificationError(report)
    return report


def reproducibility_metadata(root,seed):
    root=Path(root); source=root/'source_manifest.json'
    packages={}
    for name in ['numpy','pandas','matplotlib','vrplib','nbformat','nbclient','ipykernel','jupyter_client']:
        try: packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: packages[name]=None
    return dict(utc=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
        processor=platform.processor(),seed=seed,packages=packages,
        dataset_root=str(root.resolve()),source_manifest=json.loads(source.read_text()) if source.exists() else None,
        upstream_commit="not recorded by source manifest; use collection/per-file hashes")


def check_routing_equations(instance, x, y, z, u, tolerance=1e-7):
    """Evaluate M1–M10 on externally supplied arrays, including disconnected cycles.

    x has (K,N,N), y/u (K,n), z (K,). This small-model diagnostic is not a solver.
    """
    require_cvrptw(instance)
    if not np.isfinite(tolerance) or not 0 <= tolerance <= 1e-6: raise ValueError('Invalid tolerance')
    K=instance.max_vehicles; n=instance.n_customers; N=n+1
    arrays=[np.asarray(a,dtype=float) for a in (x,y,z,u)]
    if any(a.shape != shape or not np.all(np.isfinite(a)) for a,shape in
           zip(arrays,[(K,N,N),(K,n),(K,),(K,n)])):
        raise ValueError('Wrong routing variable shapes/nonfinite values')
    x,y,z,u=arrays
    checks={
        'binary_domains':all(np.all((abs(a)<=tolerance)|(abs(a-1)<=tolerance)) for a in (x,y,z)),
        'coverage':np.all(abs(y.sum(axis=0)-1)<=tolerance),
        'outgoing':np.all(abs(x.sum(axis=2)[:,1:]-y)<=tolerance),
        'incoming':np.all(abs(x.sum(axis=1)[:,1:]-y)<=tolerance),
        'depot_outgoing':np.all(abs(x[:,0,1:].sum(axis=1)-z)<=tolerance),
        'depot_incoming':np.all(abs(x[:,1:,0].sum(axis=1)-z)<=tolerance),
        'activation':np.all(y<=z[:,None]+tolerance),
        'capacity':np.all(y@instance.demands[1:]<=instance.capacity*z+tolerance),
        'order_bounds':np.all(u>=y-tolerance) and np.all(u<=n*y+tolerance),
        'no_self_loops':np.all(abs(np.diagonal(x,axis1=1,axis2=2))<=tolerance),
    }
    mtz=True
    mask=~np.eye(n,dtype=bool)
    for k in range(K):
        residual=u[k][None,:]-u[k][:,None]-1+(n+1)*(1-x[k,1:,1:])
        mtz=mtz and bool(np.all(residual[mask]>=-tolerance))
    checks['mtz']=mtz
    return {k:bool(v) for k,v in checks.items()}
