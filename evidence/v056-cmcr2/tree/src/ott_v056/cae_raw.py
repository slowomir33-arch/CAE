"""Raw CAE-down paired execution for OTT V. Bypasses all scalar scorers.

NON_SCIENTIFIC_TEST_FIXTURE surfaces only. Decisive 32×128 is not invoked here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import NON_SCIENTIFIC
from .grounding import GroundingRoundtripError, ground_intervention_spec
from .mapping import SYSTEMS, equality_mode, output_names
from .v_metric import (
    InfrastructureFailure,
    extract_frozen_vector,
    probe_match,
)

BOTTOM_UP_FORBIDDEN = "causal_abstraction.sampling.BottomUpSampler"


class MappingError(RuntimeError):
    pass


def _require_cae():
    try:
        from causal_abstraction.paths import DiagramBuilder
        from causal_abstraction.sampling import BottomUpSampler, TopDownSampler
    except Exception as e:
        raise MappingError(f"pinned CAE import failed: {e}") from e
    return DiagramBuilder, TopDownSampler, BottomUpSampler


def resolve_vars(high_level_model: Any, names: Sequence[str]) -> List[Any]:
    out = []
    for n in names:
        if n not in high_level_model.variables:
            raise MappingError(f"variable {n} not in high-level model")
        out.append(high_level_model.variables[n])
    return list(out)


def make_sampler(system: str, value_map: Any) -> Any:
    """D23: TopDownSampler except CPU InstructionSampler. Never BottomUpSampler."""
    _, TopDownSampler, BottomUpSampler = _require_cae()
    if system == "cpu_6502":
        from systems import cpu_6502 as cpu_mod  # type: ignore
        sampler = cpu_mod.InstructionSampler(value_map)
    else:
        sampler = TopDownSampler(value_map)
    if isinstance(sampler, BottomUpSampler) and type(sampler) is BottomUpSampler:
        raise MappingError("BottomUpSampler is forbidden for Track-A V")
    if type(sampler).__name__ == "BottomUpSampler":
        raise MappingError("BottomUpSampler is forbidden for Track-A V")
    return sampler


def complete_missing_roots(
    sampler: Any,
    intervention_spec: Dict[str, Any],
    all_roots: Sequence[Any],
    batch_size: int,
    sampler_rng: np.random.Generator,
) -> Dict[str, Any]:
    """Reproduce EvaluationEngine._process_batch_raw missing-root completion."""
    spec = dict(intervention_spec)
    missing = [r for r in all_roots if r.name not in spec]
    if missing:
        bg = sampler.sample_intervention(missing, batch_size, force_all=True, rng=sampler_rng)
        if bg:
            spec.update(bg)
    return spec


def build_standard_paths(builder: Any) -> Tuple[Any, Any]:
    """Authoritative DiagramBuilder primitives. Not combined/phi paths."""
    high = builder.build_path_standard_high_level_model()
    low = builder.build_path_standard_low_level_model()
    return high, low


def execute_paired_raw(builder: Any, intervention_spec: Dict[str, Any], path_rng: np.random.Generator) -> Tuple[Any, Any]:
    """Execute standard high and mapped-low paths. Does not score."""
    path_h, path_l = build_standard_paths(builder)
    high = path_h.execute(intervention_spec, rng=path_rng)
    low = path_l.execute(intervention_spec, rng=path_rng)
    return high, low


def sample_and_ground_probe(
    *,
    system: str,
    builder: Any,
    sampler_rng: np.random.Generator,
    ground_rng: np.random.Generator,
) -> Dict[str, Any]:
    cfg = SYSTEMS[system]
    sampler = make_sampler(system, builder.vm)
    targets = resolve_vars(builder.high_level_model, cfg["intervention_domain"])
    # Do not intervene directly on frozen outputs.
    out_set = set(cfg["frozen_outputs"])
    targets = [t for t in targets if t.name not in out_set]
    primary = sampler.sample_intervention(
        targets,
        int(cfg["batch_size"]),
        int(cfg["max_interventions"]),
        rng=sampler_rng,
    )
    spec = complete_missing_roots(
        sampler,
        dict(primary),
        builder.high_level_model.get_roots(),
        int(cfg["batch_size"]),
        sampler_rng,
    )
    return ground_intervention_spec(builder.vm, spec, ground_rng)


def evaluate_probe(
    *,
    system: str,
    builder: Any,
    sampler_rng: np.random.Generator,
    ground_rng: np.random.Generator,
    path_rng: np.random.Generator,
) -> Dict[str, Any]:
    """One non-scientific probe. Never calls CAE scalar scorers."""
    spec = sample_and_ground_probe(
        system=system,
        builder=builder,
        sampler_rng=sampler_rng,
        ground_rng=ground_rng,
    )
    high, low = execute_paired_raw(builder, spec, path_rng)
    names = output_names(system)
    mode = equality_mode(system)
    high_vec, high_st = extract_frozen_vector(high, names)
    low_vec, low_st = extract_frozen_vector(low, names)
    match = probe_match(high_vec, low_vec, mode=mode, high_status=high_st, low_status=low_st)
    return {
        NON_SCIENTIFIC: "YES",
        "frozen_outputs": list(names),
        "high_vector": high_vec,
        "low_vector": low_vec,
        "high_status": high_st,
        "low_status": low_st,
        "probe_match": match,
        "scalar_cae_metric": None,
    }


def sampler_class_name(system: str, value_map: Any) -> str:
    return type(make_sampler(system, value_map)).__name__
