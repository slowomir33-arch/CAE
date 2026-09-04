"""pytest for v0.5.6 execution-spec candidate. NON_SCIENTIFIC_TEST_FIXTURE only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ott_v056 import NON_SCIENTIFIC, SENTINEL_DOI, CAE_COMMIT
from ott_v056.canonical import (
    CanonicalError,
    cat,
    field,
    sha256_hex,
    sort_by_raw_digest,
    track_a_seed,
    track_b_split,
)
from ott_v056.paths import canonical_relative_path
from ott_v056.stages import Harness, StageError, MAPPING_STOP
from ott_v056.output import OutputError


def test_d01_rejects_surrounding_whitespace():
    with pytest.raises(CanonicalError):
        field(" a")
    with pytest.raises(CanonicalError):
        field("a ")


def test_d01_d02_field_framing_hex():
    # TEXT("ab") = 61 62; FIELD = uint32_be(2) || 61 62
    assert field("ab").hex() == "000000026162"
    assert field(0).hex() == "0000000130"
    assert field(31).hex() == "000000023331"
    with pytest.raises(CanonicalError):
        field(-1)


def test_d02_cat_no_literal_delimiter():
    c = cat("A", "B")
    assert b"||" not in c
    assert c.hex() == "00000001410000000142"


def test_d03_cae_commit_pin():
    d, pre = track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 0)
    assert CAE_COMMIT.encode("ascii") in pre
    from ott_v056.canonical import require_cae_commit
    with pytest.raises(CanonicalError):
        require_cae_commit("d91f65b5620423d3eae98478bc9843f4a40e361a")


def test_d04_zero_based_index():
    track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 0)
    track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 31)
    with pytest.raises(CanonicalError):
        track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 32)


def test_track_a_seed_vector():
    digest, pre = track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 0)
    assert pre.hex() == (
        field(SENTINEL_DOI) + field(CAE_COMMIT) + field("logic_circuit") + field("valid") + field(0)
    ).hex()
    assert digest.hex() == hashlib.sha256(pre).hexdigest()
    vec = json.loads((Path(__file__).parent / "test_vectors.json").read_text())
    assert digest.hex() == vec["track_a_seed"]["sha256"]
    assert pre.hex() == vec["track_a_seed"]["preimage_hex"]


def test_track_b_split_and_path():
    rel = canonical_relative_path("p01.hddl")
    digest, pre = track_b_split(SENTINEL_DOI, "Rover-GTOHP", rel)
    assert digest.hex() == hashlib.sha256(pre).hexdigest()
    with pytest.raises(CanonicalError):
        canonical_relative_path("./p01.hddl")
    with pytest.raises(CanonicalError):
        canonical_relative_path("/abs/p01.hddl")
    with pytest.raises(CanonicalError):
        canonical_relative_path("a/../b.hddl")


def test_d12_raw_byte_order():
    a = (bytes.fromhex("00" * 32), b"z")
    b = (bytes.fromhex("ff" * 32), b"a")
    assert sort_by_raw_digest([b, a])[0] is a


def test_collision_seed(tmp_path):
    h = Harness(tmp_path / "run", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    h.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    d, _ = track_a_seed(SENTINEL_DOI, "logic_circuit", "valid", 0)
    h.counters.seed_digests[d] = ("other", "x", 0)
    with pytest.raises(StageError, match="seed collision"):
        h.stage_a_cae([("logic_circuit", "valid")])


def test_duplicate_path(tmp_path):
    h = Harness(tmp_path / "run2", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    h.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    with pytest.raises(StageError, match="duplicate canonical"):
        h.stage_a_ipc_split([
            {"domain_id": "Transport", "canonical_relative_path": "pfile01.hddl", "file_sha256": "aa"},
            {"domain_id": "Transport", "canonical_relative_path": "pfile01.hddl", "file_sha256": "bb"},
        ])


def test_existing_dir_and_overwrite(tmp_path):
    d = tmp_path / "run3"
    d.mkdir()
    (d / "old.txt").write_text("x")
    h = Harness(d, fixture=True, doi=SENTINEL_DOI)
    with pytest.raises(OutputError):
        h.precheck()


def test_no_resume_after_start(tmp_path):
    h = Harness(tmp_path / "run4", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    h.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    with pytest.raises(StageError, match="resume"):
        h.resume_in_place()


def test_stage_a_does_not_call_b(tmp_path):
    h = Harness(tmp_path / "run5", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    h.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    h.stage_a_cae([("tracr", "fail")])
    h.stage_a_ipc_split([{"domain_id": "Woodworking", "canonical_relative_path": "12.hddl", "file_sha256": "00"}])
    h.stage_a_ipc_baseline()
    man = h.stage_a_seal()
    assert man["counters"]["candidate_selection_count"] == 0
    assert man["counters"]["held_out_count"] == 0
    assert man["counters"]["scoring_count"] == 0
    assert man["counters"]["verdict_count"] == 0
    assert man["counters"]["external_label_join_count"] == 0
    text = (tmp_path / "run5" / "stage_a_track_a.jsonl").read_text()
    assert NON_SCIENTIFIC in text
    with pytest.raises(StageError, match="STAGE_B_FORBIDDEN"):
        h.stage_b()
    # boundary proof: B increment happens only if invoked, not from A
    assert h.counters.candidate_selection_count == 1  # the failed explicit call
    # A already sealed with 0
    assert man["counters"]["candidate_selection_count"] == 0


def test_doi_null_decisive():
    h = Harness(Path("/tmp/never-v056"), fixture=False, doi=None)
    with pytest.raises(StageError, match="DOI_NULL"):
        h.precheck()


def test_real_cae_refuses_mapping(tmp_path):
    h = Harness(tmp_path / "run6", fixture=False, doi="10.5281/zenodo.0")
    with pytest.raises(StageError):
        h.precheck()
    # mapping stop on cae if someone bypassed
    h2 = Harness(tmp_path / "run7", fixture=True, doi=SENTINEL_DOI)
    h2.precheck()
    h2.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    h2.fixture = False
    with pytest.raises(StageError, match=MAPPING_STOP):
        h2.stage_a_cae([("logic_circuit", "valid")])


def test_output_order_replicates_then_probes(tmp_path):
    h = Harness(tmp_path / "run8", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    h.start_stage_a({
        "RUN_ID": "T", "UTC": "2026-09-04T00:00:00Z",
        "protocol_root": "00", "runtime_digest": "sha256:00",
        "execution_spec_hash": "00",
    })
    h.stage_a_cae([("grn", "valid")])
    rows = [json.loads(x) for x in (tmp_path / "run8" / "stage_a_track_a.jsonl").read_text().splitlines()]
    pairs = [(r["replicate_index"], r["probe_index"]) for r in rows]
    assert pairs == [(r, p) for r in range(32) for p in range(128)]


def test_jsonl_canonical_separators(tmp_path):
    h = Harness(tmp_path / "run9", fixture=True, doi=SENTINEL_DOI)
    h.precheck()
    line = (tmp_path / "run9" / "PRECHECK.json").read_text()
    assert " : " not in line
    assert ", " not in line
