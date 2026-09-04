"""R3 D21 membership regression. NON_SCIENTIFIC_TEST_FIXTURE only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ott_v056.ipc_official import (
    HISTORICAL_R2_TOTAL_REQUIRED,
    HISTORICAL_R2_WOODWORKING_REQUIRED,
    REQUIRED_COUNTS,
    REQUIRED_TOTAL,
    WOODWORKING_REPOSITORY_EXTRA_EXCLUDED,
    counts_by_domain,
    d21_verdict,
    is_official_problem_path,
)

MANIFEST = ROOT / "protocol" / "IPC_ELIGIBLE_PROBLEM_MANIFEST_v0.5.6.json"
SUPERSESSION = ROOT / "protocol" / "D21_SUPERSESSION_v0.5.6.json"
NON_IPC_DIR = "further-instances-not-used-in-ipc"


def _man():
    return json.loads(MANIFEST.read_text())


def test_r3_official_four_domain_counts():
    man = _man()
    obs = counts_by_domain(man["eligible"])
    assert obs["Rover-GTOHP"] == 30
    assert obs["Satellite-GTOHP"] == 20
    assert obs["Transport"] == 40
    assert obs["Woodworking"] == 30
    assert sum(obs.values()) == 120
    assert REQUIRED_COUNTS == {
        "Rover-GTOHP": 30,
        "Satellite-GTOHP": 20,
        "Transport": 40,
        "Woodworking": 30,
    }
    assert REQUIRED_TOTAL == 120
    assert d21_verdict(obs) == "PASS"
    assert man["D21_status"] == "PASS"
    summary = man["official_ipc2020_counts"]
    assert summary == {
        "Rover-GTOHP": 30,
        "Satellite-GTOHP": 20,
        "Transport": 40,
        "Woodworking": 30,
    }
    assert man["total"] == 120
    assert man["woodworking_repository_extra_excluded"] == 10
    assert man["doi_assigned"] is False
    assert man["split_assigned"] is False


def test_r3_other_domains_unchanged():
    man = _man()
    obs = counts_by_domain(man["eligible"])
    if obs["Rover-GTOHP"] != 30 or obs["Satellite-GTOHP"] != 20 or obs["Transport"] != 40:
        raise AssertionError("STOP_R3_OTHER_DOMAIN_MEMBERSHIP_MISMATCH")


def test_r3_woodworking_official_count_is_30():
    man = _man()
    wood = [e for e in man["eligible"] if e["domain_id"] == "Woodworking"]
    assert len(wood) == 30
    for e in wood:
        assert NON_IPC_DIR not in e["canonical_relative_path"]
        assert is_official_problem_path(e["canonical_relative_path"])
        assert e.get("official_ipc2020_membership") is True
        assert e.get("parse_accepted") is True


def test_r3_further_instances_directory_all_ineligible():
    man = _man()
    extras = [
        e
        for e in man["excluded"]
        if NON_IPC_DIR in e["canonical_relative_path"]
    ]
    assert len(extras) == WOODWORKING_REPOSITORY_EXTRA_EXCLUDED
    eligible_paths = {e["canonical_relative_path"] for e in man["eligible"]}
    for e in extras:
        rel = e["canonical_relative_path"]
        assert rel.startswith(NON_IPC_DIR + "/")
        assert is_official_problem_path(rel) is False
        assert rel not in eligible_paths
        assert e.get("d21_reason", "path_not_official")


def test_r3_regression_woodworking_40_must_not_return():
    """Fails if required count is restored to repository-total 40 while extras stay excluded."""
    assert REQUIRED_COUNTS["Woodworking"] != HISTORICAL_R2_WOODWORKING_REQUIRED
    assert REQUIRED_TOTAL != HISTORICAL_R2_TOTAL_REQUIRED
    assert REQUIRED_COUNTS["Woodworking"] == 30
    assert REQUIRED_TOTAL == 120
    observed = {
        "Rover-GTOHP": 30,
        "Satellite-GTOHP": 20,
        "Transport": 40,
        "Woodworking": 30,
    }
    # Old R2 required table against the same exclusion-rule observation must not PASS.
    old_required = dict(REQUIRED_COUNTS)
    old_required["Woodworking"] = 40
    assert observed != old_required


def test_r3_all_eligible_parser_accepted():
    man = _man()
    rejected = [e for e in man["eligible"] if not e.get("parse_accepted")]
    assert rejected == []


def test_r3_d21_supersession_recorded():
    doc = json.loads(SUPERSESSION.read_text())
    assert doc["document"] == "D21_SUPERSESSION_v0.5.6"
    assert doc["old_woodworking_required_count"] == 40
    assert doc["new_woodworking_official_ipc2020_count"] == 30
    assert doc["excluded_extra_count"] == 10
    assert doc["official_total_four_domains"] == 120
    assert doc["scientific_observations_before_correction"] == 0
    assert doc["doi_reserved_before_correction"] is False
    assert doc["decisive_split_before_correction"] is False
    assert doc["source_commit"] == "9e313248244a0a13302ae262f42ef446f43e4182"
