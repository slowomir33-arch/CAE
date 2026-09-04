"""P1 DOI-binding tests. NON_SCIENTIFIC_TEST_FIXTURE only. No real-DOI randomization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESERVED = "10.5281/zenodo.22293061"
SENTINEL = "10.0000/OTT-V0.5.6-TEST-DO-NOT-PUBLISH"
MAPPING_SHA = "48b3fa3059e55cde2794209db62cd00a348cc04200253525e084fff023506d52"
RUNTIME_REF = (
    "ghcr.io/slowomir33-arch/cae-ott-v055-runtime@"
    "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
)
FP_ROOT = "166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271"
PLACEHOLDERS = {
    None,
    "",
    "null",
    "NOT_RESERVED",
    "TBD",
    "TODO",
    "10.5281/zenodo.xxxxxxxx",
    "10.5281/zenodo.0",
}


def _j(rel: str):
    return json.loads((ROOT / rel).read_text())


def _sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def test_p1_reserved_doi_in_every_required_final_field():
    spec = _j("protocol/execution_spec_v0.5.6.json")
    seed = _j("protocol/seed_policy_v0.5.6.json")
    tmpl = _j("protocol/RUN_AUTHORIZATION.template.json")
    receipt = _j("ZENODO_DOI_RESERVATION_RECEIPT.json")
    meta = _j("ZENODO_PUBLICATION_METADATA.json")
    readme = (ROOT / "README.md").read_text()
    assert spec["PUBLIC_V0_5_6_DOI"] == RESERVED
    assert seed["public_v0_5_6_DOI"] == RESERVED
    assert tmpl["public_v0_5_6_DOI"] == RESERVED
    assert receipt["reserved_doi"] == RESERVED
    assert meta["reserved_doi"] == RESERVED
    assert f"`{RESERVED}`" in readme


def test_p1_no_placeholder_in_final_public_fields():
    spec = _j("protocol/execution_spec_v0.5.6.json")
    seed = _j("protocol/seed_policy_v0.5.6.json")
    tmpl = _j("protocol/RUN_AUTHORIZATION.template.json")
    for value in (
        spec["PUBLIC_V0_5_6_DOI"],
        seed["public_v0_5_6_DOI"],
        tmpl["public_v0_5_6_DOI"],
    ):
        assert value not in PLACEHOLDERS
        assert value == RESERVED
        assert value != SENTINEL


def test_p1_no_real_doi_derived_seed_split_artifacts():
    forbidden_names = {
        "TRACK_A_SEEDS.json",
        "TRACK_A_REPLICATE_SEEDS.json",
        "IPC_SPLIT.json",
        "IPC_SPLIT_MEMBERSHIP.json",
        "DOI_SALTED_SEEDS.json",
        "DOI_SALTED_SPLIT.json",
        "BASELINE_LEDGER.json",
        "CANDIDATE_SELECTION.json",
        "HELD_OUT_RESULTS.json",
        "H1_H4_VERDICT.json",
        "RUN_AUTHORIZATION.json",
    }
    found = [p.name for p in ROOT.rglob("*") if p.is_file() and p.name in forbidden_names]
    assert found == []
    # Sentinel vectors must remain sentinel; no real-DOI digest rows.
    vec = _j("tests/test_vectors.json")
    rng = _j("protocol/NUMPY_RNG_TEST_VECTORS_v0.5.6.json")
    assert vec["sentinel_doi"] == SENTINEL
    assert vec["track_a_seed"]["doi"] == SENTINEL
    assert rng["doi"] == SENTINEL
    assert RESERVED not in json.dumps(vec)
    assert RESERVED not in json.dumps(rng)


def test_p1_ipc_manifest_remains_120():
    man = _j("protocol/IPC_ELIGIBLE_PROBLEM_MANIFEST_v0.5.6.json")
    assert man["total"] == 120
    assert man["official_ipc2020_counts"] == {
        "Rover-GTOHP": 30,
        "Satellite-GTOHP": 20,
        "Transport": 40,
        "Woodworking": 30,
    }
    assert man["doi_assigned"] is False
    assert man["split_assigned"] is False
    assert man["D21_status"] == "PASS"


def test_p1_d08_mapping_hash_unchanged():
    assert _sha("protocol/CAE_EXECUTION_MAPPING_v0.5.6.json") == MAPPING_SHA


def test_p1_runtime_binding_unchanged():
    bind = _j("protocol/runtime_binding_v0.5.6.json")
    spec = _j("protocol/execution_spec_v0.5.6.json")
    assert bind["final_runtime_immutable_ref"] == RUNTIME_REF
    assert bind["final_runtime_fingerprint_root"] == FP_ROOT
    assert spec["runtime"] == RUNTIME_REF
    assert spec["fingerprint_root"] == FP_ROOT


def test_p1_no_run_authorization_json():
    assert not (ROOT / "RUN_AUTHORIZATION.json").exists()
    assert not (ROOT / "protocol" / "RUN_AUTHORIZATION.json").exists()
    hits = list(ROOT.rglob("RUN_AUTHORIZATION.json"))
    assert hits == []


def test_p1_publication_status_draft_unpublished():
    receipt = _j("ZENODO_DOI_RESERVATION_RECEIPT.json")
    meta = _j("ZENODO_PUBLICATION_METADATA.json")
    spec = _j("protocol/execution_spec_v0.5.6.json")
    assert receipt["published"] is False
    assert receipt["submitted"] is False
    assert receipt["doi_registered_as_published"] is False
    assert receipt["draft_status"] == "unpublished/unsubmitted"
    assert receipt["zenodo_environment"] == "production"
    assert meta["published"] is False
    assert spec["zenodo_publication"] is False


def test_p1_delta_unexpected_zero():
    led = _j("DOI_INSERTION_DELTA_LEDGER.json")
    assert led["unexpected_count"] == 0
    assert led["UNEXPECTED"] == []
    assert led["R3_TO_P1_SCIENTIFIC_SEMANTICS_CHANGE"] == 0


def test_p1_sentinel_doi_unchanged_in_harness():
    from ott_v056 import SENTINEL_DOI

    assert SENTINEL_DOI == SENTINEL
