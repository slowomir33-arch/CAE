"""Stage surfaces. Stage A must never call B–E. Decisive 32×128 is not authorized."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import NON_SCIENTIFIC, SENTINEL_DOI
from .canonical import CanonicalError, sha256_hex, track_a_seed, track_b_split
from .output import OutputError, dumps_scientific, jsonl_line, require_empty_run_dir, write_new
from .paths import canonical_relative_path

MAPPING_STOP = "STOP_IMPLEMENTATION_MAPPING_AMBIGUOUS"  # historical R1 token; unused in R2
MAPPING_RESOLVED = "CAE_down_exact_vector_V"
DOI_NULL_STOP = "REAL_DECISIVE_MODE_DOI_NULL"
DECISIVE_FORBIDDEN = "DECISIVE_32x128_NOT_AUTHORIZED"


class StageError(RuntimeError):
    pass


@dataclass
class Counters:
    candidate_selection_count: int = 0
    held_out_count: int = 0
    external_label_join_count: int = 0
    scoring_count: int = 0
    verdict_count: int = 0
    start_stage_a: bool = False
    sealed: bool = False
    units: List[str] = field(default_factory=list)
    seed_digests: Dict[bytes, tuple] = field(default_factory=dict)
    split_digests: Dict[bytes, tuple] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, int]:
        return {
            "candidate_selection_count": self.candidate_selection_count,
            "held_out_count": self.held_out_count,
            "external_label_join_count": self.external_label_join_count,
            "scoring_count": self.scoring_count,
            "verdict_count": self.verdict_count,
        }


def _unit_id(*parts: str) -> str:
    return "|".join(parts)


class Harness:
    def __init__(self, run_dir: Path, *, fixture: bool, doi: Optional[str]):
        self.run_dir = Path(run_dir)
        self.fixture = fixture
        self.doi = doi
        self.counters = Counters()
        self.started = False
        self.incidents: List[str] = []

    def precheck(self) -> Dict[str, Any]:
        if self.started:
            raise StageError("precheck after START_STAGE_A forbidden")
        if not self.fixture:
            if not self.doi:
                raise StageError(DOI_NULL_STOP)
            raise StageError("decisive precheck not authorized in this candidate stage")
        if self.doi != SENTINEL_DOI:
            raise CanonicalError("fixture mode requires sentinel DOI")
        require_empty_run_dir(self.run_dir)
        receipt = {
            NON_SCIENTIFIC: "YES",
            "doi": self.doi,
            "status": "PRECHECK_OK",
            "cae_mapping": MAPPING_RESOLVED,
        }
        write_new(self.run_dir / "PRECHECK.json", (dumps_scientific(receipt) + "\n").encode("utf-8"))
        return receipt

    def start_stage_a(self, identities: Dict[str, Any]) -> Dict[str, Any]:
        if not self.fixture:
            raise StageError("START_STAGE_A decisive mode not authorized")
        doc = {
            NON_SCIENTIFIC: "YES",
            "RUN_ID": identities["RUN_ID"],
            "UTC": identities["UTC"],
            "public_DOI": self.doi,
            "protocol_root": identities["protocol_root"],
            "runtime_digest": identities["runtime_digest"],
            "execution_spec_hash": identities["execution_spec_hash"],
            "output_directory": str(self.run_dir.resolve()),
        }
        raw = (dumps_scientific(doc) + "\n").encode("utf-8")
        write_new(self.run_dir / "START_STAGE_A.json", raw)
        doc_hash = sha256_hex(raw)
        write_new(self.run_dir / "START_STAGE_A.sha256", (doc_hash + "\n").encode("ascii"))
        self.started = True
        self.counters.start_stage_a = True
        return {"sha256": doc_hash, "document": doc}

    def stage_a_cae(self, systems_conditions: List[tuple]) -> None:
        self._require_started()
        if not self.fixture:
            raise StageError(DECISIVE_FORBIDDEN)
        out = self.run_dir / "stage_a_track_a.jsonl"
        if out.exists():
            raise OutputError("refusing overwrite")
        lines = []
        for system, condition in systems_conditions:
            for rep in range(32):
                digest, pre = track_a_seed(self.doi, system, condition, rep)
                if digest in self.counters.seed_digests:
                    prev = self.counters.seed_digests[digest]
                    cur = (system, condition, rep)
                    if prev != cur:
                        raise StageError("seed collision across distinct tuples")
                self.counters.seed_digests[digest] = (system, condition, rep)
                for probe in range(128):
                    uid = _unit_id("A", system, condition, str(rep), str(probe))
                    if uid in self.counters.units:
                        raise StageError("duplicate Stage-A unit ID")
                    self.counters.units.append(uid)
                    rec = {
                        "condition": condition,
                        "error_class": None,
                        "probe_index": probe,
                        "protocol_id": "v0.5.6-candidate",
                        "raw_payload_sha256": None,
                        "replicate_index": rep,
                        "replicate_seed_sha256": digest.hex(),
                        "run_id": "FIXTURE",
                        "runtime_id": "FIXTURE",
                        "status": "FIXTURE_NOT_EXECUTED",
                        "system": system,
                        "timing_ms": None,
                    }
                    lines.append(jsonl_line(rec, fixture=True))
        write_new(out, "".join(lines).encode("utf-8"))

    def stage_a_ipc_split(self, problems: List[Dict[str, str]]) -> None:
        self._require_started()
        if not self.fixture:
            raise StageError("decisive IPC split not authorized")
        out = self.run_dir / "stage_a_track_b.jsonl"
        if out.exists():
            raise OutputError("refusing overwrite")
        seen_paths = set()
        rows = []
        keyed = []
        for item in problems:
            domain = item["domain_id"]
            rel = canonical_relative_path(item["canonical_relative_path"])
            key = (domain, rel)
            if key in seen_paths:
                raise StageError("duplicate canonical problem path")
            seen_paths.add(key)
            digest, pre = track_b_split(self.doi, domain, rel)
            if digest in self.counters.split_digests:
                prev = self.counters.split_digests[digest]
                if prev != key:
                    raise StageError("split-digest collision across distinct inputs")
            self.counters.split_digests[digest] = key
            keyed.append((digest, rel.encode("utf-8"), domain, rel, item.get("file_sha256")))
        keyed.sort(key=lambda t: (t[0], t[1]))
        # D12: sort then keep first 20 per domain is decisive; fixture only records digest+order
        by_domain: Dict[str, int] = {}
        for digest, _pb, domain, rel, fsha in keyed:
            n = by_domain.get(domain, 0)
            if n < 8:
                split = "development"
            elif n < 20:
                split = "evaluation"
            else:
                split = "excluded_over_cap"
            by_domain[domain] = n + 1
            rec = {
                "assigned_split": split,
                "canonical_path": rel,
                "domain": domain,
                "error_class": None,
                "file_sha256": fsha,
                "raw_planner_output_sha256": None,
                "split_digest_sha256": digest.hex(),
                "status": "FIXTURE_NOT_EXECUTED",
                "timing_ms": None,
            }
            rows.append(jsonl_line(rec, fixture=True))
        write_new(out, "".join(rows).encode("utf-8"))

    def stage_a_ipc_baseline(self) -> None:
        self._require_started()
        if not self.fixture:
            raise StageError("decisive IPC baseline not authorized")
        # sentinel tiny fixture: record that baseline was not converted from INFRA
        write_new(
            self.run_dir / "baseline_fixture.json",
            (dumps_scientific({NON_SCIENTIFIC: "YES", "SOLVED": 0, "UNSOLVED": 0, "INFRASTRUCTURE_FAILURE": 0, "note": "no planner invoked"}) + "\n").encode("utf-8"),
        )

    def stage_a_seal(self) -> Dict[str, Any]:
        self._require_started()
        files = []
        for p in sorted(self.run_dir.rglob("*")):
            if p.is_file() and p.name not in {"manifest.json"}:
                files.append({"path": str(p.relative_to(self.run_dir)), "bytes": p.stat().st_size, "sha256": sha256_hex(p.read_bytes())})
        man = {NON_SCIENTIFIC: "YES", "files": files, "counters": self.counters.as_dict()}
        write_new(self.run_dir / "manifest.json", (dumps_scientific(man) + "\n").encode("utf-8"))
        self.counters.sealed = True
        return man

    def stage_b(self) -> None:
        self.counters.candidate_selection_count += 1
        raise StageError("STAGE_B_FORBIDDEN: candidate selection not authorized")

    def stage_c(self) -> None:
        self.counters.held_out_count += 1
        raise StageError("STAGE_C_FORBIDDEN")

    def stage_d(self) -> None:
        self.counters.external_label_join_count += 1
        self.counters.scoring_count += 1
        raise StageError("STAGE_D_FORBIDDEN")

    def stage_e(self) -> None:
        self.counters.verdict_count += 1
        raise StageError("STAGE_E_FORBIDDEN")

    def resume_in_place(self) -> None:
        if self.started:
            raise StageError("in-place resume after START_STAGE_A forbidden (D18)")
        raise StageError("resume forbidden")

    def _require_started(self) -> None:
        if not self.started:
            raise StageError("START_STAGE_A required")
