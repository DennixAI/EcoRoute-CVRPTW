"""Configuration of the ALNS + VND solver.

Every algorithmic setting is a field here; ``ALNSConfig.from_dict`` rejects
unknown keys so that a typo in an experiment plan cannot silently fall back to a
default.  Defaults are the frozen tuned values (dev campaigns dev-001..dev-007,
see results/alns-vnd/README.md).
"""
from dataclasses import asdict, dataclass, fields
import math

DESTROY_OPERATORS = ("random", "worst", "shaw", "string", "route")
REPAIR_OPERATORS = ("greedy", "regret2", "regret3", "blink")
NEIGHBOURHOODS = ("relocate", "swap", "two_opt_star", "or_opt", "two_opt")


@dataclass(frozen=True)
class ALNSConfig:
    # --- stopping ---------------------------------------------------------
    # Fraction of the wall-clock limit the search may use, and an absolute
    # reserve (seconds) for returning the result.  clock="call" measures the
    # budget from the solve() call; clock="process" measures it from the start
    # of the current process (needs psutil), which is what the isolated
    # benchmark worker enforces: interpreter start-up and imports are charged.
    clock: str = "call"
    time_fraction: float = 0.97
    time_reserve: float = 0.75
    max_iterations: int = 0            # 0 = unlimited (time-limited only)
    # deterministic=True (requires max_iterations): annealing schedule and time
    # checks follow the iteration count, so a seed always gives the same
    # solution on any machine; the time limit is only a safety cap.
    deterministic: bool = False
    chunk_seconds: float = 0.05        # granularity of time checks

    # --- granular neighbourhoods -------------------------------------------
    n_neighbours: int = 40             # repair: routes of these neighbours are candidates
    vnd_neighbours: int = 20           # VND: neighbours v examined per customer u
    near_list: int = 100               # SISR adjacency length
    shaw_list: int = 100               # Shaw relatedness list length
    tw_wait_weight: float = 0.2        # proximity: penalty on forced waiting
    tw_warp_weight: float = 1.0        # proximity: penalty on lateness
    insert_all_routes: bool = False    # repair: scan every route (slow, n<=200)

    # --- destroy ------------------------------------------------------------
    destroy_min: int = 5
    destroy_max: int = 40
    destroy_max_fraction: float = 0.2  # q_max = min(destroy_max, frac * n)
    worst_randomness: float = 3.0      # p in y^p (Ropke & Pisinger)
    shaw_randomness: float = 6.0
    shaw_weights: tuple = (9.0, 3.0, 2.0)  # distance, time window, demand
    sisr_avg_removed: float = 10.0     # c-bar
    sisr_max_string: int = 10          # L_max
    sisr_split_rate: float = 0.5
    sisr_split_depth: float = 0.01     # beta
    blink_rate: float = 0.01

    # --- adaptive operator selection ---------------------------------------
    destroy_weights: tuple = (1.0, 0.0, 1.0, 1.0, 0.5)   # 0 disables (worst off: tuned)
    repair_weights: tuple = (1.0, 1.0, 1.0, 1.0)
    score_new_best: float = 33.0
    score_better: float = 9.0
    score_accepted: float = 13.0
    reaction: float = 0.1
    segment: int = 100

    # --- acceptance / diversification ---------------------------------------
    # Simulated annealing with temperatures relative to the mean arc length of
    # the initial solution, cooled exponentially over the elapsed budget.
    temp_start: float = 1.5
    temp_end: float = 0.02
    restart_after: int = 0             # iterations without best improvement; 0 = off

    # --- VND ----------------------------------------------------------------
    neighbourhoods: tuple = NEIGHBOURHOODS

    def __post_init__(self):
        def positive(name, integer=False, allow_zero=False):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if integer and int(value) != value:
                raise ValueError(f"{name} must be an integer")
            if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
                raise ValueError(f"{name} must be {'nonnegative' if allow_zero else 'positive'}")
        for name in ("time_fraction", "chunk_seconds", "destroy_max_fraction", "worst_randomness",
                     "shaw_randomness", "sisr_avg_removed", "temp_start", "temp_end"):
            positive(name)
        for name in ("time_reserve", "tw_wait_weight", "tw_warp_weight", "blink_rate", "score_new_best",
                     "score_better", "score_accepted", "sisr_split_rate", "sisr_split_depth"):
            positive(name, allow_zero=True)
        for name in ("n_neighbours", "vnd_neighbours", "near_list", "shaw_list", "destroy_min", "destroy_max",
                     "sisr_max_string"):
            positive(name, integer=True)
        for name in ("max_iterations", "segment", "restart_after"):
            positive(name, integer=True, allow_zero=True)
        if not isinstance(self.deterministic, bool):
            raise ValueError("deterministic must be True or False")
        if self.deterministic and not self.max_iterations:
            raise ValueError("deterministic=True requires max_iterations > 0")
        if self.clock not in ("call", "process"):
            raise ValueError("clock must be 'call' or 'process'")
        if self.time_fraction > 1:
            raise ValueError("time_fraction must be <= 1")
        if not 0 < self.reaction <= 1:
            raise ValueError("reaction must be in (0, 1]")
        if self.destroy_min > self.destroy_max:
            raise ValueError("destroy_min must not exceed destroy_max")
        if self.temp_end > self.temp_start:
            raise ValueError("temp_end must not exceed temp_start")
        if not 0 <= self.blink_rate < 1 or not 0 <= self.sisr_split_rate <= 1 or not 0 <= self.sisr_split_depth < 1:
            raise ValueError("probabilities out of range")
        for name, names in (("destroy_weights", DESTROY_OPERATORS), ("repair_weights", REPAIR_OPERATORS)):
            weights = getattr(self, name)
            if len(weights) != len(names) or any(not math.isfinite(w) or w < 0 for w in weights) or sum(weights) <= 0:
                raise ValueError(f"{name} needs {len(names)} nonnegative weights, not all zero ({names})")
        if len(self.shaw_weights) != 3 or any(w < 0 for w in self.shaw_weights):
            raise ValueError("shaw_weights = (distance, time, demand) nonnegative")
        if not self.neighbourhoods or any(nb not in NEIGHBOURHOODS for nb in self.neighbourhoods) \
                or len(set(self.neighbourhoods)) != len(self.neighbourhoods):
            raise ValueError(f"neighbourhoods must be distinct names from {NEIGHBOURHOODS}")

    @classmethod
    def from_dict(cls, values=None):
        values = dict(values or {})
        known = {f.name for f in fields(cls)}
        unknown = set(values) - known
        if unknown:
            raise ValueError(f"Unknown ALNS configuration keys: {sorted(unknown)}")
        for key in ("shaw_weights", "destroy_weights", "repair_weights", "neighbourhoods"):
            if key in values:
                values[key] = tuple(values[key])
        return cls(**values)

    def to_dict(self):
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items()}
