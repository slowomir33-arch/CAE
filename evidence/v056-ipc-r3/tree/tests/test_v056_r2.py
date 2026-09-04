"""v0.5.6 candidate R2 tests: D08/D19–D24, T1–T6. NON_SCIENTIFIC_TEST_FIXTURE only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ott_v056 import CAE_COMMIT, NON_SCIENTIFIC, SENTINEL_DOI
from ott_v056.canonical import track_a_seed
from ott_v056.grounding import GroundingRoundtripError, ground_intervention_spec
from ott_v056.ipc_official import (
    REQUIRED_COUNTS,
    counts_by_domain,
    d21_verdict,
    is_official_problem_path,
)
from ott_v056.mapping import PRIMARY_CONDITIONS, SYSTEMS
from ott_v056.rng import (
    RUNTIME_NUMPY_VERSION,
    digest_to_entropy_words,
    first_draws,
    generators_for_probe,
    spawn_key_list,
    spawn_probe_sequences,
)
from ott_v056.v_metric import (
    GRN_ATOL,
    InfrastructureFailure,
    V_replicate,
    extract_frozen_vector,
    grn_equal,
    probe_match,
)

VECTORS = json.loads((Path(__file__).parent / "test_vectors.json").read_text())
RNG_PATH = ROOT / "protocol" / "NUMPY_RNG_TEST_VECTORS_v0.5.6.json"


def _logic_bundle():
    repo = Path("/workspace")
    if not (repo / "systems" / "01_logic_circuit.py").exists():
        repo = Path("/opt/ott/sources/CAE")
    test_dir = repo / "test"
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from utils import load_system
    from causal_abstraction import EvaluationConfig, MicroVariableSchema
    from causal_abstraction.paths import DiagramBuilder

    lc = load_system("01_logic_circuit.py", "logic_circuit_sys")
    gates, all_wires = lc.build_2bit_adder()
    schema = MicroVariableSchema.from_names(all_wires)
    low_level = lc.NetlistSimulator(gates, all_wires)
    cg, vm = lc.build_cg_and_vm(schema)
    high = lc.build_valid_high_level_model()
    builder = DiagramBuilder(high, low_level, vm, cg, EvaluationConfig(metric="hard"))
    return builder, vm, high


def test_d21_excludes_further_instances_and_generators():
    assert is_official_problem_path("p01.hddl")
    assert is_official_problem_path("12.hddl")
    assert not is_official_problem_path("further-instances-not-used-in-ipc/31.hddl")
    assert not is_official_problem_path("other/create_woodworking_instance.py")
    assert not is_official_problem_path("domain.hddl")
    assert not is_official_problem_path("README.md")


def test_d21_manifest_counts_match_ipc2020_evaluation_population():
    man = json.loads((ROOT / "protocol" / "IPC_ELIGIBLE_PROBLEM_MANIFEST_v0.5.6.json").read_text())
    kept = man["eligible"]
    obs = counts_by_domain(kept)
    assert REQUIRED_COUNTS["Woodworking"] == 30
    assert REQUIRED_COUNTS["Woodworking"] != 40
    assert man["D21_status"] == "PASS"
    assert d21_verdict(obs) == "PASS"
    assert obs["Rover-GTOHP"] == 30
    assert obs["Satellite-GTOHP"] == 20
    assert obs["Transport"] == 40
    assert obs["Woodworking"] == 30
    assert sum(obs.values()) == 120
    for row in kept:
        assert is_official_problem_path(row["canonical_relative_path"])
        assert "further-instances-not-used-in-ipc" not in row["canonical_relative_path"]
        assert row.get("parse_accepted") is True
        assert row.get("official_ipc2020_membership") is True


def test_d19_rng_vectors_match_runtime_numpy():
    assert np.__version__ == RUNTIME_NUMPY_VERSION
    doc = json.loads(RNG_PATH.read_text())
    assert doc["numpy_version"] == RUNTIME_NUMPY_VERSION
    digest = bytes.fromhex(doc["replicate_sha256"])
    assert digest_to_entropy_words(digest) == doc["entropy_words"]
    from ott_v056.rng import probe_stream_sequences

    probes = spawn_probe_sequences(digest)
    for idx in ("0", "1", "127"):
        i = int(idx)
        rec = doc["probes"][idx]
        ss = probes[i]
        assert spawn_key_list(ss) == rec["probe_spawn_key"]
        sampler_ss, ground_ss, path_ss = probe_stream_sequences(ss)
        streams = rec["streams"]
        assert spawn_key_list(sampler_ss) == streams["SAMPLER"]["spawn_key"]
        assert spawn_key_list(ground_ss) == streams["GROUND"]["spawn_key"]
        assert spawn_key_list(path_ss) == streams["PATH"]["spawn_key"]
        sampler_rng, ground_rng, path_rng = generators_for_probe(digest, i)
        assert first_draws(sampler_rng) == streams["SAMPLER"]["first_draws"]
        assert first_draws(ground_rng) == streams["GROUND"]["first_draws"]
        assert first_draws(path_rng) == streams["PATH"]["first_draws"]


def test_d19_uses_sentinel_track_a_digest():
    digest, pre = track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 0)
    doc = json.loads(RNG_PATH.read_text())
    assert digest.hex() == doc["replicate_sha256"]
    assert pre.hex() == doc["replicate_preimage_hex"]
    assert CAE_COMMIT.encode("ascii") in pre


def test_d20_seeded_grounding_roundtrip():
    class VM:
        def ground(self, name, label, rng=None):
            _ = float(rng.random())
            return np.array([float(label)], dtype=np.float64)

        def abstract(self, name, micro_values):
            return int(np.asarray(micro_values).reshape(-1)[0])

    rng = np.random.default_rng(0)
    spec = {"Operand_A": {"labels": [2], "micro_values": None}}
    out = ground_intervention_spec(VM(), spec, rng)
    assert out["Operand_A"]["micro_values"].shape[0] == 1
    assert int(out["Operand_A"]["micro_values"].reshape(-1)[0]) == 2


def test_d20_roundtrip_failure_does_not_resample():
    n = {"ground": 0}

    class BadVM:
        def ground(self, name, label, rng=None):
            n["ground"] += 1
            _ = rng.random()
            return np.array([99.0])

        def abstract(self, name, micro_values):
            return 99

    with pytest.raises(GroundingRoundtripError, match="STOP_GROUNDING_ROUNDTRIP_FAILURE"):
        ground_intervention_spec(
            BadVM(),
            {"X": {"labels": [1], "micro_values": None}},
            np.random.default_rng(1),
        )
    assert n["ground"] == 1


def test_t4_full_vector_atomicity():
    assert probe_match([1, 2], [1, 2], mode="exact") == 1
    assert probe_match([1, 2], [1, 3], mode="exact") == 0
    assert probe_match([1, 2], [1, 3], mode="exact") != 0.5


def test_t5_grn_tolerance_and_nan():
    assert grn_equal(0.0, GRN_ATOL / 2) is True
    assert grn_equal(0.0, GRN_ATOL) is True
    assert grn_equal(0.0, GRN_ATOL + 1e-12) is False
    # rtol = 0: relative closeness of large values is not a match
    assert grn_equal(1.0e10, 1.0e10 + 1.0) is False
    assert grn_equal(float("nan"), 0.0) is False
    assert grn_equal(0.0, float("nan")) is False
    assert grn_equal(float("nan"), float("nan")) is False
    with pytest.raises(InfrastructureFailure, match="non-finite"):
        extract_frozen_vector({"fz_tgt": [float("nan")]}, ["fz_tgt"])


def test_t6_unmapped_is_non_match():
    high = {"Y": [1]}
    low = {"Y": ["UNMAPPED"]}
    hv, hs = extract_frozen_vector(high, ["Y"])
    lv, ls = extract_frozen_vector(low, ["Y"], nonfinite_is_infrastructure=False)
    assert probe_match(hv, lv, mode="exact", high_status=hs, low_status=ls) == 0
    hv2, hs2 = extract_frozen_vector({"Y": [1]}, ["Y"])
    lv2, ls2 = extract_frozen_vector({}, ["Y"])
    assert ls2 == ["missing"]
    assert probe_match(hv2, lv2, mode="exact", high_status=hs2, low_status=ls2) == 0


def test_v_is_mean_of_128_bits():
    bits = [1] * 64 + [0] * 64
    assert V_replicate(bits) == 0.5
    with pytest.raises(InfrastructureFailure):
        V_replicate([1] * 10)


def test_t2_scalar_metrics_not_used_for_v(monkeypatch):
    called = []

    def boom(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("scalar CAE metric used for V")

    import causal_abstraction.engine as engine_mod
    from causal_abstraction.metrics import MSEMetric
    from causal_abstraction.analytical_metrics import DCCMetric, IIAMetric

    monkeypatch.setattr(engine_mod.EvaluationEngine, "_score_collected_results", boom)
    monkeypatch.setattr(MSEMetric, "measure", boom)
    monkeypatch.setattr(IIAMetric, "compute", boom)
    monkeypatch.setattr(DCCMetric, "compute", boom)

    from ott_v056.cae_raw import evaluate_probe
    from ott_v056.rng import generators_for_probe

    builder, _, _ = _logic_bundle()
    digest = bytes.fromhex(VECTORS["track_a_seed"]["sha256"])
    s, g, p = generators_for_probe(digest, 0)
    rec = evaluate_probe(system="logic_circuit", builder=builder, sampler_rng=s, ground_rng=g, path_rng=p)
    assert rec["scalar_cae_metric"] is None
    assert rec["probe_match"] in (0, 1)
    assert called == []
    assert rec[NON_SCIENTIFIC] == "YES"


def test_t3_not_bottom_up():
    from causal_abstraction.sampling import BottomUpSampler, TopDownSampler
    from ott_v056.cae_raw import make_sampler

    builder, vm, _ = _logic_bundle()
    sampler = make_sampler("logic_circuit", vm)
    assert isinstance(sampler, TopDownSampler)
    assert not isinstance(sampler, BottomUpSampler)
    assert SYSTEMS["cpu_6502"]["sampler_callable"].endswith("InstructionSampler")
    assert "BottomUp" not in SYSTEMS["logic_circuit"]["sampler_callable"]
    assert SYSTEMS["tracr"]["sampler_callable"].endswith("TopDownSampler")
    assert SYSTEMS["grn"]["sampler_callable"].endswith("TopDownSampler")


def test_t1_path_identity():
    from ott_v056.cae_raw import execute_paired_raw
    from ott_v056.grounding import ground_intervention_spec

    builder, vm, _ = _logic_bundle()
    spec0 = {
        "Operand_A": {"labels": [2], "micro_values": None},
        "Operand_B": {"labels": [1], "micro_values": None},
        "Carry_In": {"labels": [1], "micro_values": None},
    }
    spec = ground_intervention_spec(vm, spec0, np.random.default_rng(123))
    ss = np.random.SeedSequence([7, 8, 9])
    h_ott, l_ott = execute_paired_raw(builder, spec, np.random.default_rng(ss))
    rng = np.random.default_rng(ss)
    h_dir = builder.build_path_standard_high_level_model().execute(spec, rng=rng)
    l_dir = builder.build_path_standard_low_level_model().execute(spec, rng=rng)
    names = ["Result_Sum", "Result_Carry"]
    hv1, _ = extract_frozen_vector(h_ott, names)
    hv2, _ = extract_frozen_vector(h_dir, names)
    lv1, _ = extract_frozen_vector(l_ott, names)
    lv2, _ = extract_frozen_vector(l_dir, names)
    assert hv1 == hv2
    assert lv1 == lv2


def test_d24_primary_conditions_match_sealed_adapter():
    assert PRIMARY_CONDITIONS["logic_circuit"]["positive"] == ["valid"]
    assert PRIMARY_CONDITIONS["logic_circuit"]["negative"] == ["fail", "inv_internal"]
    assert PRIMARY_CONDITIONS["tracr"]["negative"] == ["fail"]
    assert PRIMARY_CONDITIONS["grn"]["negative"] == ["wrong_map", "wrong_high_level_model"]
    assert PRIMARY_CONDITIONS["cpu_6502"]["positive"] == [
        "valid_gate_isa",
        "valid_transistor_gate",
        "valid_transistor_isa",
    ]
    assert SYSTEMS["tracr"]["frozen_outputs"] == ["rank_0", "rank_1", "rank_2"]
    assert SYSTEMS["cpu_6502"]["frozen_outputs"] == ["A_out", "X_out", "Y_out", "S_out", "P_out"]
    from pathlib import Path as P

    text = P("/workspace/systems/10_cpu_6502.py").read_text()
    assert 'OUTPUTS  = ["A_out","X_out","Y_out","S_out","P_out"]' in text
    ttext = P("/workspace/systems/08_tracr.py").read_text()
    assert "SEQ_LEN = 3" in ttext
