"""Static CVRPTW modeling checks. No route construction or optimization."""
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import hashlib
import importlib.metadata
import platform
import sys
import numpy as np
import pandas as pd

FAMILY_COUNTS = {"Solomon": 56, "GH200": 60, "GH400": 60, "GH600": 60, "GH800": 60, "GH1000": 60}

@dataclass
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

    def __post_init__(self):
        # Normalize containers, but never silently fix wrong shapes or depot service.
        for key in ("demands", "distances", "time_windows", "service_durations", "coordinates", "travel_times"):
            value = getattr(self, key)
            if value is not None:
                setattr(self, key, np.asarray(value, dtype=float))
        if self.original_ids is not None: self.original_ids = np.asarray(self.original_ids)
        if self.distance_tenths is not None: self.distance_tenths = np.asarray(self.distance_tenths)
        if self.travel_times is None and self.distances is not None:
            self.travel_times = self.distances.copy()  # Selected native convention t=d.

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
        if self.original_ids is not None and (self.original_ids.shape != (N,) or len(set(self.original_ids.tolist())) != N):
            errors.append("Optional original IDs must be unique and length N")
        ticks = self.distance_tenths
        if ticks is not None:
            if ticks.shape != (N,N) or ticks.dtype.kind not in "iu" or np.any(ticks < 0):
                errors.append("Optional distance_tenths must be nonnegative integer (N,N)")
            elif self.distances is not None and self.distances.shape == (N,N) and not np.allclose(ticks/10,self.distances,rtol=0,atol=1e-12):
                errors.append("distance_tenths disagrees with distances")
        return errors

def dimacs_tenths(xy):
    """Truncate, never round. Correct sqrt boundaries exactly for integer coordinates."""
    xy = np.asarray(xy, dtype=float)
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
    service = np.asarray(value,dtype=float)
    if service.ndim == 0:
        if not np.isfinite(service) or service < 0: raise ValueError("Invalid scalar SERVICE_TIME")
        service = np.full(N,float(service)); service[0] = 0
    elif service.shape != (N,): raise ValueError("SERVICE_TIME must be scalar or length N")
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
    xy=np.asarray(raw["node_coord"],dtype=float)
    if xy.shape != (N,2) or not np.all(np.isfinite(xy)): raise ValueError("Invalid coordinates")
    if str(raw.get("edge_weight_type","")).upper() != "EUC_2D": raise ValueError("Unsupported edge type")
    K=float(raw["vehicles"])
    if not np.isfinite(K) or not K.is_integer(): raise ValueError("Noninteger VEHICLES")
    ticks=dimacs_tenths(xy)
    inst=CVRPTWInstance(name=str(raw.get("name",path.stem)),demands=raw["demand"],capacity=float(raw["capacity"]),
        max_vehicles=int(K),distances=ticks/10,coordinates=xy,original_ids=ids,
        time_windows=raw["time_window"],service_durations=normalize_service(raw["service_time"],N),
        distance_tenths=ticks,source=str(path),distance_policy="dimacs_truncate_1_decimal")
    if inst.check_input(): raise ValueError(inst.check_input())
    return inst

def check_cvrptw(instance,routes,departure_times=None,tolerance=1e-7):
    """Audit supplied orders at supplied depot departures; never search for orders."""
    if instance.check_input(): raise ValueError(instance.check_input())
    if not np.isfinite(tolerance) or not 0 <= tolerance <= 1e-6: raise ValueError("Tolerance must be in [0,1e-6] benchmark units")
    if not isinstance(routes,(list,tuple)): raise ValueError("Routes must be sequences")
    errors=[]; active=[]; seen=[]
    for r in routes:
        if not isinstance(r,(list,tuple,np.ndarray)) or np.ndim(r)!=1:
            errors.append("Malformed route"); continue
        if len(r): active.append(list(r))
    if len(active)>instance.max_vehicles: errors.append("Fleet limit exceeded")
    if departure_times is None: departure_times=[instance.time_windows[0,0]]*len(active)
    if len(departure_times)!=len(active): raise ValueError("One departure per nonempty route required")
    schedules=[]; totals=[]; distances=[]; N=instance.n_customers+1
    for k,(r,T) in enumerate(zip(active,departure_times),1):
        if any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) or not 1<=i<N for i in r):
            errors.append(f"Truck {k}: invalid customer IDs"); continue
        seen.extend(r); T=float(T)
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
            cost=sum(int(instance.distance_tenths[i,j]) for i,j in zip(path,path[1:]))/10
        else: cost=sum(float(instance.distances[i,j]) for i,j in zip(path,path[1:]))
        distances.append(cost); schedules.append(pd.DataFrame(rows))
        totals.append(dict(truck=k,departure=T,return_time=t,elapsed=t-T,driving=driving,waiting=waiting,service=service,
            load=load,utilization=load/instance.capacity,distance=cost,depot_lateness=max(0.,t-H)))
    counts=Counter(seen)
    if set(seen)!=set(range(1,N)): errors.append("Missing customer coverage")
    if any(v!=1 for v in counts.values()): errors.append("Duplicate customers")
    # Undefined cost for malformed/invalid output; no deceptively favorable score.
    return dict(feasible=not errors,errors=errors,distance=sum(distances) if not errors else None,
        schedules=schedules,route_totals=pd.DataFrame(totals),tolerance=tolerance,
        active_routes=active,departure_times=list(departure_times))

def check_temporal_equations(instance,routes,audit):
    """Evaluate EVERY selected and inactive temporal arc for EVERY vehicle slot.

    Identical all-zero inactive slots are checked once, with multiplicity recorded.
    No sampled nodes. Vectorized one-vehicle matrices bound peak memory to O(N²).
    """
    if not audit["feasible"]: return False
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
        assert np.all(y<=z)
        for a in (A,S,D): assert np.all(a>=-tol) and np.all(a<=H*y+tol)
        assert np.all(S[1:]>=A[1:]-tol)
        assert np.all(S[1:]>=instance.time_windows[1:,0]*y[1:]-tol)
        assert np.all(S[1:]<=instance.time_windows[1:,1]*y[1:]+tol)
        assert np.allclose(D[1:],S[1:]+instance.service_durations[1:]*y[1:],rtol=0,atol=tol)
        assert instance.time_windows[0,0]*z-tol<=T<=R+tol and R<=H*z+tol
        origin=D.copy(); origin[0]=T
        target=A.copy(); target[0]=R
        residual=target[None,:]-origin[:,None]-travel
        bound=(H+travel)*(~x)
        mask=~np.eye(N,dtype=bool)
        assert np.all(np.abs(residual[mask])<=bound[mask]+tol)
        checked+=N*(N-1)*(1 if z else K-len(active))
    assert checked==K*N*(N-1)
    return True

def verify_collection(root,strict=False):
    """All paired references, all data constraints and costs; not benchmarking."""
    import vrplib
    root=Path(root); missing=[]; paths=[]
    for family,count in FAMILY_COUNTS.items():
        vrps=sorted((root/family).glob("*.vrp")); sols=list((root/family).glob("*.sol"))
        if len(vrps)!=count or {p.stem for p in vrps}!={p.stem for p in sols}:
            missing.append(f"{family}: expected {count} matched pairs, found {len(vrps)} inputs/{len(sols)} solutions")
        paths.extend((family,p) for p in vrps)
    if missing:
        if strict: raise FileNotFoundError('; '.join(missing))
        return dict(status="NOT RUN",reason='; '.join(missing),checked=0,results=pd.DataFrame())
    records=[]; digest=hashlib.sha256()
    for family,path in paths:
        inst=load_cvrptw(path); sol=path.with_suffix('.sol'); ref=vrplib.read_solution(str(sol))
        routes=[list(r) for r in ref['routes']]  # NO shifting, coercing or seeding search.
        audit=check_cvrptw(inst,routes)
        if not audit['feasible']: raise AssertionError((path.name,audit['errors']))
        if 'cost' not in ref or not np.isfinite(float(ref['cost'])): raise ValueError(f'Missing reference cost: {sol}')
        if abs(audit['distance']-float(ref['cost']))>1e-7: raise AssertionError((path.name,audit['distance'],ref['cost']))
        record=dict(family=family,instance=inst.name,n=inst.n_customers,K=inst.max_vehicles,Q=inst.capacity,
            reference_routes=len(routes),distance=audit['distance'],supplied_cost=float(ref['cost']),feasible=True,
            input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(sol.read_bytes()).hexdigest())
        records.append(record)
        digest.update(f"{family}/{path.name}:{record['input_sha256']}:{record['reference_sha256']}\n".encode())
    return dict(status="PASS",checked=len(records),results=pd.DataFrame(records),collection_sha256=digest.hexdigest())

def reproducibility_metadata(root,seed):
    import json
    root=Path(root); source=root/'source_manifest.json'
    return dict(python=sys.version,platform=platform.platform(),seed=seed,
        packages={m:importlib.metadata.version(m) for m in ['numpy','pandas','matplotlib','vrplib']},
        dataset_root=str(root.resolve()),source_manifest=json.loads(source.read_text()) if source.exists() else None,
        upstream_commit="not recorded by source manifest; use collection/per-file hashes")
