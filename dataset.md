# EcoRoute — CVRPTW dataset guide

## Collection

The checked-in benchmark collection is [`benchmarks/vrptw/`](benchmarks/vrptw/), downloaded from [PyVRP/Instances](https://github.com/PyVRP/Instances/tree/main/VRPTW). It contains **356 distinct problem instances** and **356 paired published solutions**:

| Folder | Customers per instance | `.vrp` inputs | `.sol` references |
| --- | ---: | ---: | ---: |
| `Solomon/` | 100 | 56 | 56 |
| `GH200/` | 200 | 60 | 60 |
| `GH400/` | 400 | 60 | 60 |
| `GH600/` | 600 | 60 | 60 |
| `GH800/` | 800 | 60 | 60 |
| `GH1000/` | 1,000 | 60 | 60 |

Every `.vrp` describes a vehicle routing instance with capacity and time windows. A `.sol` file contains published routes and a reference cost; it is **not** a second problem instance or an output from our algorithm. The folders also contain the upstream README, license, and `source_manifest.json` with archive provenance. The manifest records an archive hash but does not pin an upstream commit or hash every individual file.

## File format and indexing

The `.vrp` files are PyVRP-converted **VRPLIB** format. Read fields such as `DIMENSION`, `VEHICLES`, `CAPACITY`, `SERVICE_TIME`, coordinates, demands, and time windows from each file. `DIMENSION` includes the depot: `C101.vrp` has 101 nodes and 100 customers. Fleet size and capacity vary by instance; never hard-code them.

On disk, the `.vrp` depot is node `1` and customers are nodes `2..N`. Normalize the depot to array index `0` and customers to `1..n` internally. The paired `.sol` route labels are customer numbers `1..n`, so they line up with the normalized indices. Check this mapping before evaluating a reference route.

The source coordinates are synthetic Cartesian points. Published reference costs use the source's **DIMACS one-decimal truncation** of distances and durations. Verify the evaluator by reproducing `Solomon/C101.sol` (cost `827.3`) and a Gehring–Homberger example before computing gaps. A `.sol` cost does not by itself prove optimality.

## Download and load

The files are already checked in. To download the selected collection again, run:

```bash
python scripts/download_vrptw_benchmarks.py
```

The script writes to `benchmarks/vrptw/` relative to the repository, independent of the shell's working directory. It selects only the VRPTW files, verifies the expected family counts and matching `.vrp`/`.sol` pairs, and writes a source manifest. An upstream archive change may change the files on a future run; preserve hashes for published experiments.

The selected `.vrp` files use the default `vrplib` VRPLIB parser, **not** the parser for historical Solomon text files:

```python
from pathlib import Path
import vrplib

root = Path("benchmarks/vrptw")
instance = vrplib.read_instance(str(root / "Solomon" / "C101.vrp"))
reference = vrplib.read_solution(str(root / "Solomon" / "C101.sol"))

assert int(instance["dimension"]) == 101
assert int(instance["vehicles"]) > 0
assert float(instance["capacity"]) > 0
```

Check the actual keys and shapes after parsing. `SERVICE_TIME` may be a scalar; normalize it into per-node service durations for the evaluator. Keep route labels, normalized indices, and depot timing explicit.

## Feasibility and evaluation

Each customer must be served exactly once. Every used route starts and ends at the depot, respects capacity, starts customer service within each hard window, and returns within the depot window. Early arrival permits waiting. The evaluator should independently recompute feasibility and cost from route sequences, rather than trusting a solver's status flag.

Use separate development and held-out instances. The final evaluation needs at least **20 distinct instances**; repeated random seeds on one instance do not increase that count. Record source hash, instance name, reference cost and convention, route count, feasibility, distance, runtime, and seed for every run. See [`benchmarks.md`](benchmarks.md) for the reporting protocol.
