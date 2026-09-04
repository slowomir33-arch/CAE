"""D20: seed value_map.ground before the mapped-low-level standard path."""
from __future__ import annotations

from typing import Any, Dict, Mapping

import numpy as np

from .v_metric import InfrastructureFailure, exact_equal, is_unmapped


class GroundingRoundtripError(RuntimeError):
    """STOP_GROUNDING_ROUNDTRIP_FAILURE"""


STOP_GROUNDING_ROUNDTRIP_FAILURE = "STOP_GROUNDING_ROUNDTRIP_FAILURE"


def _as_label(label: Any) -> Any:
    if isinstance(label, np.generic):
        return label.item()
    if isinstance(label, np.ndarray) and label.size == 1:
        return label.reshape(-1)[0].item() if hasattr(label.reshape(-1)[0], "item") else label.reshape(-1)[0]
    return label


def _shape_micro_for_path(val: np.ndarray, *, batch_size: int) -> np.ndarray:
    """Match pinned DiagramBuilder._step_ground_or_passthrough batch-1 reshape."""
    val = np.asarray(val)
    if batch_size > 1:
        return val
    if val.ndim == 0:
        return val.reshape(1, 1)
    if val.ndim == 1:
        return val[np.newaxis, :]
    return val


def labels_match_declared(abstracted: Any, sampled_label: Any) -> bool:
    sampled_label = _as_label(sampled_label)
    if is_unmapped(abstracted):
        return False
    if isinstance(abstracted, np.generic):
        abstracted = abstracted.item()
    return exact_equal(abstracted, sampled_label) or abstracted == sampled_label


def ground_intervention_spec(
    value_map: Any,
    intervention_spec: Mapping[str, Any],
    ground_rng: np.random.Generator,
) -> Dict[str, Any]:
    """Populate micro_values via value_map.ground(..., rng=GROUND_RNG). Do not resample on failure."""
    out: Dict[str, Any] = {}
    for name, data in intervention_spec.items():
        entry = dict(data)
        labels = entry.get("labels")
        if labels is None:
            out[name] = entry
            continue
        if not isinstance(labels, (list, tuple, np.ndarray)):
            labels = [labels]
        else:
            labels = list(labels)
        batch_size = len(labels)
        grounded_list = []
        for lbl in labels:
            lbl = _as_label(lbl)
            try:
                mv = value_map.ground(name, lbl, rng=ground_rng)
            except Exception as e:
                raise InfrastructureFailure(f"value_map.ground failed for {name}: {e}") from e
            try:
                back = value_map.abstract(name, mv)
            except Exception as e:
                raise InfrastructureFailure(f"value_map.abstract failed for {name}: {e}") from e
            if not labels_match_declared(back, lbl):
                raise GroundingRoundtripError(
                    f"{STOP_GROUNDING_ROUNDTRIP_FAILURE}: {name} tau(ground({lbl!r}))={back!r}"
                )
            grounded_list.append(np.asarray(mv))
        if batch_size == 1:
            stacked = _shape_micro_for_path(grounded_list[0], batch_size=1)
        else:
            stacked = np.stack(grounded_list)
        entry["labels"] = labels
        entry["micro_values"] = stacked
        out[name] = entry
    return out
