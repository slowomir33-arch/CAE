"""Frozen Track-A mapping table for v0.5.6 candidate R2. No scalar CAE metric."""
from __future__ import annotations

from typing import Any, Dict, List

CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
ORIENTATION = "CAE_down / top-down"
SCALAR_CAE_METRIC = None
OTT_REDUCTION = "custom_exact_vector_V"

PRIMARY_CONDITIONS = {
    "logic_circuit": {
        "positive": ["valid"],
        "negative": ["fail", "inv_internal"],
        "excluded_noise": ["noise"],
    },
    "tracr": {
        "positive": ["valid"],
        "negative": ["fail"],
        "excluded_noise": ["noise"],
    },
    "grn": {
        "positive": ["valid"],
        "negative": ["wrong_map", "wrong_high_level_model"],
        "excluded_noise": ["noise"],
    },
    "cpu_6502": {
        "positive": ["valid_gate_isa", "valid_transistor_gate", "valid_transistor_isa"],
        "negative": ["broken_gate_isa", "broken_transistor_gate", "broken_transistor_isa"],
        "excluded_noise": [],
    },
}

SYSTEMS: Dict[str, Dict[str, Any]] = {
    "logic_circuit": {
        "module": "systems/01_logic_circuit.py",
        "sampler_callable": "causal_abstraction.sampling.TopDownSampler",
        "intervention_domain": ["Operand_A", "Operand_B", "Carry_In", "Internal_Carries"],
        "max_interventions": 2,
        "batch_size": 1,
        "frozen_outputs": ["Result_Sum", "Result_Carry"],
        "equivalence": "exact",
        "equality_mode": "exact",
        "upstream_test": "test/01_logic_circuit.py",
        "high_level_constructors": {
            "valid": "build_valid_high_level_model",
            "fail": "build_failing_high_level_model",
            "inv_internal": "build_inverted_internal_high_level_model",
        },
        "low_level_constructor": "NetlistSimulator",
        "cg_vm_builder": "build_cg_and_vm",
    },
    "tracr": {
        "module": "systems/08_tracr.py",
        "sampler_callable": "causal_abstraction.sampling.TopDownSampler",
        "intervention_domain": ["token_0", "token_1", "token_2"],
        "max_interventions": 3,
        "batch_size": 1,
        "frozen_outputs": ["rank_0", "rank_1", "rank_2"],
        "equivalence": "exact",
        "equality_mode": "exact",
        "upstream_test": "test/08_tracr.py",
        "SEQ_LEN": 3,
        "high_level_constructors": {
            "valid": "_build_high_level_model(_make_rank_equation)",
            "fail": "_build_high_level_model(_make_failing_rank_equation)",
        },
        "low_level_constructor": "TracrLowLevelModel",
        "cg_vm_builder": "_build_shared_maps",
    },
    "grn": {
        "module": "systems/09_grn/grn.py",
        "sampler_callable": "causal_abstraction.sampling.TopDownSampler",
        "intervention_domain": ["wg_src"],
        "max_interventions": 1,
        "batch_size": 1,
        "frozen_outputs": ["fz_tgt"],
        "equivalence": "abs(a-b)<=1e-9 rtol=0",
        "equality_mode": "grn",
        "upstream_test": "test/09_grn.py",
        "high_level_constructors": {
            "valid": "valid high-level model",
            "wrong_map": "wrong CG map condition",
            "wrong_high_level_model": "reversed high-level rule",
        },
        "low_level_constructor": "GRN low-level model",
        "cg_vm_builder": "GRN value map / CG map builders",
    },
    "cpu_6502": {
        "module": "systems/10_cpu_6502.py",
        "sampler_callable": "systems/10_cpu_6502.py::InstructionSampler",
        "intervention_domain": ["A_in", "X_in", "Y_in", "S_in", "P_in", "opcode", "operand"],
        "max_interventions": 7,
        "batch_size": 1,
        "frozen_outputs": ["A_out", "X_out", "Y_out", "S_out", "P_out"],
        "equivalence": "exact",
        "equality_mode": "exact",
        "upstream_test": "test/10_cpu_6502.py",
        "high_level_constructors": {
            "valid_gate_isa": "ISA high-level vs gate low-level",
            "valid_transistor_gate": "gate high-level vs transistor low-level",
            "valid_transistor_isa": "ISA high-level vs transistor low-level",
            "broken_gate_isa": "broken gate vs ISA",
            "broken_transistor_gate": "broken transistor vs gate",
            "broken_transistor_isa": "broken transistor vs ISA",
        },
        "low_level_constructor": "layer-specific simulator",
        "cg_vm_builder": "CPU CG/value maps in systems/10_cpu_6502.py",
    },
}


def system_config(system: str) -> Dict[str, Any]:
    return SYSTEMS[system]


def output_names(system: str) -> List[str]:
    return list(SYSTEMS[system]["frozen_outputs"])


def equality_mode(system: str) -> str:
    return str(SYSTEMS[system]["equality_mode"])
