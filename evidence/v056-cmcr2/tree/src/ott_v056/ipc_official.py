"""D21: official IPC 2020 TO eligibility (not parser-only)."""
from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Tuple

REQUIRED_COUNTS = {
    "Rover-GTOHP": 30,
    "Satellite-GTOHP": 20,
    "Transport": 40,
    "Woodworking": 40,
}
REQUIRED_TOTAL = 130
STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH = "STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH"
EXCLUDED_DIR_MARKERS = ("further-instances-not-used-in-ipc",)
EXCLUDED_DIR_NAMES = {"other"}
EXCLUDED_FILENAMES = {"domain.hddl", "readme.md", "makefile"}


def is_official_problem_path(canonical_relative_path: str) -> bool:
    rel = canonical_relative_path.replace("\\", "/")
    if rel.strip() != rel:
        return False
    parts = rel.split("/")
    if any(m in p for p in parts for m in EXCLUDED_DIR_MARKERS):
        return False
    if any(p.lower() in EXCLUDED_DIR_NAMES for p in parts[:-1]):
        return False
    name = parts[-1]
    if name.lower() in EXCLUDED_FILENAMES:
        return False
    if not name.lower().endswith(".hddl"):
        return False
    if name.lower() == "domain.hddl":
        return False
    return True


def filter_official(entries: Iterable[Mapping]) -> Tuple[List[dict], List[dict]]:
    kept: List[dict] = []
    excluded: List[dict] = []
    for item in entries:
        rel = item["canonical_relative_path"]
        rec = dict(item)
        if not is_official_problem_path(rel):
            rec["d21_excluded"] = True
            excluded.append(rec)
            continue
        if not rec.get("parse_accepted"):
            rec["d21_excluded"] = True
            rec["d21_reason"] = "parser_rejected"
            excluded.append(rec)
            continue
        rec["d21_excluded"] = False
        rec["official_ipc2020_membership"] = True
        kept.append(rec)
    return kept, excluded


def counts_by_domain(entries: Iterable[Mapping]) -> Dict[str, int]:
    out = {k: 0 for k in REQUIRED_COUNTS}
    for item in entries:
        d = item["domain_id"]
        if d in out:
            out[d] += 1
    return out


def d21_verdict(observed: Mapping[str, int]) -> str:
    if dict(observed) != dict(REQUIRED_COUNTS):
        return STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH
    if sum(observed.values()) != REQUIRED_TOTAL:
        return STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH
    return "PASS"
