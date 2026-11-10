"""Optional Numba JIT.

The kernels are ordinary Python functions written in the Numba-compatible
subset.  When Numba is installed they are compiled to machine code (and cached
on disk, so later processes skip compilation); otherwise, or with
``ECOROUTE_DISABLE_JIT=1``, the very same source runs as plain (slow) Python.
"""
import os

JIT_ENABLED = False
if os.environ.get("ECOROUTE_DISABLE_JIT", "") != "1":
    try:
        import numba  # noqa: F401
        JIT_ENABLED = True
    except ImportError:  # pragma: no cover - exercised only without numba
        JIT_ENABLED = False

if JIT_ENABLED:
    from numba import njit as _numba_njit

    def _cacheable(function):
        # Numba can only cache code that lives in a real source file; this is why
        # the notebook writes its solver cells to outputs/alns_build.
        return os.path.isfile(function.__code__.co_filename)

    def njit(function=None, inline=False):
        # inline=True inlines at Numba-IR level: removes call overhead (array
        # reference counting) for tiny hot helpers.
        if function is None:
            return lambda f: njit(f, inline)
        cache = _cacheable(function)
        if inline:
            return _numba_njit(cache=cache, error_model="numpy", inline="always")(function)
        # cache=True writes compiled machine code beside this package so that a
        # freshly spawned benchmark worker does not pay compilation inside its
        # time budget; error_model='numpy' avoids Python-style ZeroDivision checks.
        return _numba_njit(cache=cache, error_model="numpy")(function)
else:
    def njit(function=None, inline=False):
        if function is None:
            return lambda f: f
        return function
