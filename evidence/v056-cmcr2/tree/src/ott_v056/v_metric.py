"""Exact full-vector V. Not MSE, IIA, DCC, or any CAE scalar scorer."""
from __future__ import annotations

import math
from typing import Any, Iterable, List, Optional, Sequence, Tuple

GRN_ATOL = 1e-9
GRN_RTOL = 0.0
UNMAPPED_TOKEN = "UNMAPPED"


class InfrastructureFailure(RuntimeError):
    """D06/D22: exception or mandatory non-finite output STOPs; not probe_match=0."""


def is_unmapped(value: Any) -> bool:
    if value is None:
        return False
    try:
        from causal_abstraction.primitives import UNMAPPED
    except Exception:
        UNMAPPED = None
    if UNMAPPED is not None and value is UNMAPPED:
        return True
    if value == UNMAPPED_TOKEN:
        return True
    if isinstance(value, (list, tuple)):
        return any(is_unmapped(x) for x in value)
    return False


def _as_python_scalar(value: Any) -> Any:
    if is_unmapped(value):
        return UNMAPPED_TOKEN
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            raise InfrastructureFailure("empty batched output component")
        return _as_python_scalar(value[0])
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            if value.size == 0:
                raise InfrastructureFailure("empty ndarray output component")
            return _as_python_scalar(value.reshape(-1)[0])
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    return value


def extract_component(result: Any, name: str) -> Tuple[Any, str]:
    """Return (value, status) where status is ok|missing|unmapped."""
    if not isinstance(result, dict) or name not in result:
        return None, "missing"
    raw = result[name]
    if is_unmapped(raw):
        return UNMAPPED_TOKEN, "unmapped"
    return _as_python_scalar(raw), "ok"


def _is_nonfinite(value: Any) -> bool:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return False
    return not math.isfinite(x)


def extract_frozen_vector(
    result: Any,
    names: Sequence[str],
    *,
    nonfinite_is_infrastructure: bool = True,
) -> Tuple[List[Any], List[str]]:
    """Extract declared outputs in frozen order. status per component."""
    vec: List[Any] = []
    statuses: List[str] = []
    for name in names:
        val, st = extract_component(result, name)
        if st == "ok" and nonfinite_is_infrastructure and _is_nonfinite(val):
            raise InfrastructureFailure(f"non-finite mandatory output {name}")
        vec.append(val)
        statuses.append(st)
    return vec, statuses


def exact_equal(a: Any, b: Any) -> bool:
    if is_unmapped(a) or is_unmapped(b):
        return False
    if a is None or b is None:
        return False
    if _is_nonfinite(a) or _is_nonfinite(b):
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    try:
        if type(a) is type(b):
            return a == b
    except Exception:
        pass
    try:
        fa, fb = float(a), float(b)
        if _is_nonfinite(fa) or _is_nonfinite(fb):
            return False
        if float(int(fa)) == fa and float(int(fb)) == fb:
            return int(fa) == int(fb)
        return fa == fb
    except (TypeError, ValueError, OverflowError):
        return a == b


def grn_equal(a: Any, b: Any) -> bool:
    """abs(a-b) <= 1e-9 with rtol=0. NaN is never equal."""
    if is_unmapped(a) or is_unmapped(b):
        return False
    if a is None or b is None:
        return False
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if _is_nonfinite(fa) or _is_nonfinite(fb):
        return False
    return abs(fa - fb) <= GRN_ATOL


def component_equal(a: Any, b: Any, *, mode: str) -> bool:
    if mode == "grn":
        return grn_equal(a, b)
    if mode == "exact":
        return exact_equal(a, b)
    raise ValueError(f"unknown equality mode {mode}")


def probe_match(
    high_vec: Sequence[Any],
    low_vec: Sequence[Any],
    *,
    mode: str,
    high_status: Optional[Sequence[str]] = None,
    low_status: Optional[Sequence[str]] = None,
) -> int:
    """Full-vector Bernoulli: 1 iff every declared component matches. Never 0.5."""
    if len(high_vec) != len(low_vec):
        return 0
    if not high_vec:
        return 0
    if high_status is not None:
        if any(s != "ok" for s in high_status):
            return 0
    if low_status is not None:
        if any(s != "ok" for s in low_status):
            return 0
    for a, b in zip(high_vec, low_vec):
        if not component_equal(a, b, mode=mode):
            return 0
    return 1


def V_replicate(matches: Iterable[int]) -> float:
    matches = list(matches)
    if len(matches) != 128:
        raise InfrastructureFailure("V requires exactly 128 probe_match bits")
    return sum(int(x) for x in matches) / 128.0
