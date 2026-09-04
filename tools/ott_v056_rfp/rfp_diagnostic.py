#!/usr/bin/env python3
"""OTT v0.5.6 runtime-fingerprint PRESTART diagnostic. Runs inside the immutable image.

NO Stage A. NO START_STAGE_A. NO RUN_AUTHORIZATION consumption.
NO VERSION_DOI seeds. NO IPC split. Does not modify the image.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
FP_ROOT = "166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271"
FP_JSON_SHA = "8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd"
AUTH_SHA = "cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26"
PARENT_STAGE_A_RUN_ID = "OTT-v0.5.6-SCA-20260904T133624Z-33FAE80C"
GITHUB_PARENT_RUN_ID = "33878994052"
RECEIPTS = Path(os.environ.get("OTT_RECEIPTS_DIR", "/ott/receipts"))
SKIP_DIRS = { "/proc", "/sys", "/dev", "/ott/receipts", "/ott/gha" }
KNOWN = [
    Path("/opt/ott"),
    Path("/opt/ott/runtime"),
    Path("/opt/ott/fingerprint"),
    Path("/opt/ott/evidence"),
    Path("/opt/ott/fingerprints"),
    Path("/opt/ott/sources"),
    Path("/workspace"),
    Path("/workspace/evidence"),
    Path("/root"),
    Path("/usr/local/share"),
]
BASENAME_NEEDLES = ("fingerprint", "runtime_fingerprint", "runtime-fingerprint")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b", re.I)


class Stop(Exception):
    def __init__(self, code: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self.code = code
        self.extra = extra or {}
        super().__init__(code)


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_json(name: str, obj: Any) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / name).write_text(dumps(obj), encoding="utf-8")


def write_text(name: str, text: str) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / name).write_text(text, encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def preview_text(raw: bytes) -> Optional[str]:
    head = raw[:4096]
    try:
        return head.decode("utf-8")
    except Exception:
        return None


def basename_hit(name: str) -> bool:
    low = name.lower()
    return any(n in low for n in BASENAME_NEEDLES)


# ---------------------------------------------------------------------------
# Verbatim Stage-A locator (copied from stage_a_executor_v0.5.6._fingerprint_check)
# Do not change search roots, size cap, or match rules.
# ---------------------------------------------------------------------------
def _fingerprint_check() -> Dict[str, Any]:
    hits: List[Path] = []
    explicit = [
        Path("/opt/ott/FINGERPRINT.json"),
        Path("/opt/ott/FINGERPRINT_ROOT.txt"),
        Path("/opt/ott/runtime_fingerprint.json"),
        Path("/opt/ott/RUNTIME_FINGERPRINT.json"),
        Path("/opt/ott/fingerprint/FINGERPRINT.json"),
        Path("/opt/ott/runtime/FINGERPRINT.json"),
    ]
    for p in explicit:
        if p.is_file():
            hits.append(p)
    for root in (Path("/opt/ott"), Path("/workspace")):
        if not root.exists():
            continue
        try:
            for p in root.rglob("*fingerprint*"):
                if p.is_file() and p.stat().st_size < 2_000_000:
                    hits.append(p)
                if len(hits) > 40:
                    break
        except Exception:
            pass
    matched_json = None
    matched_root = None
    for p in hits:
        try:
            raw = p.read_bytes()
        except Exception:
            continue
        if sha256_bytes(raw) == FP_JSON_SHA:
            matched_json = str(p)
        if FP_ROOT in raw.decode("utf-8", errors="replace"):
            matched_root = str(p)
        try:
            obj = json.loads(raw.decode("utf-8"))
            blob = json.dumps(obj)
            if FP_ROOT in blob:
                matched_root = str(p)
        except Exception:
            pass
    if matched_root is None or matched_json is None:
        for p in list(Path("/opt/ott").glob("*.json")) + list(Path("/opt/ott").glob("*/*.json")):
            if not p.is_file() or p.stat().st_size >= 2_000_000:
                continue
            try:
                raw = p.read_bytes()
            except Exception:
                continue
            if sha256_bytes(raw) == FP_JSON_SHA:
                matched_json = str(p)
            if FP_ROOT in raw.decode("utf-8", errors="replace"):
                matched_root = str(p)
            hits.append(p)
    uname = os.uname()
    plat = {
        "sysname": uname.sysname,
        "machine": uname.machine,
        "release": uname.release,
    }
    if uname.sysname != "Linux" or uname.machine not in {"x86_64", "amd64"}:
        raise Stop("STOP_RFP_PARENT_OCI_IDENTITY_FAILURE", {"platform": plat})
    return {
        "platform": plat,
        "fingerprint_file_sha_match": matched_json,
        "fingerprint_root_seen_in": matched_root,
        "fingerprint_root_required": FP_ROOT,
        "fingerprint_json_sha_required": FP_JSON_SHA,
        "candidate_files": [str(p) for p in hits[:20]],
        "candidate_files_all": [str(p) for p in hits],
    }


def skip_dir(path: str) -> bool:
    for skip in SKIP_DIRS:
        if path == skip or path.startswith(skip + "/"):
            return True
    return False


def record_file(path: Path, *, hashed: bool, raw: Optional[bytes]) -> Dict[str, Any]:
    st = path.stat()
    rec: Dict[str, Any] = {
        "absolute_path": str(path),
        "bytes": st.st_size,
        "file_type": "file",
        "basename": path.name,
        "basename_fingerprint": basename_hit(path.name),
    }
    data = raw
    if data is None and st.st_size <= 8_000_000:
        try:
            data = path.read_bytes()
        except Exception as e:
            rec["read_error"] = f"{type(e).__name__}: {e}"
            return rec
    if hashed and data is not None:
        rec["sha256"] = sha256_bytes(data)
    elif hashed and st.st_size <= 10_000_000:
        try:
            rec["sha256"] = sha256_file(path)
        except Exception as e:
            rec["sha256_error"] = f"{type(e).__name__}: {e}"
    if data is not None:
        rec["contains_fp_root"] = FP_ROOT.encode("ascii") in data or FP_ROOT in data.decode("utf-8", errors="replace")
        rec["preview_utf8_4kib"] = preview_text(data)
        rec["sha256"] = rec.get("sha256") or sha256_bytes(data)
    else:
        rec["contains_fp_root"] = False
        rec["preview_utf8_4kib"] = None
        rec["sha_scan_skipped_too_large"] = True
    rec["exact_json_sha"] = rec.get("sha256") == FP_JSON_SHA
    return rec


def exhaustive_search() -> Dict[str, Any]:
    sha_hits: List[Dict[str, Any]] = []
    root_hits: List[Dict[str, Any]] = []
    name_hits: List[Dict[str, Any]] = []
    scanned = 0
    hashed = 0
    errors = 0
    for dirpath, dirnames, filenames in os.walk("/", followlinks=False):
        if skip_dir(dirpath):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not skip_dir(os.path.join(dirpath, d))]
        for name in filenames:
            scanned += 1
            p = Path(dirpath) / name
            try:
                st = p.lstat()
            except Exception:
                errors += 1
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            want_name = basename_hit(name)
            want_hash = st.st_size <= 2_000_000 or want_name
            want_content = st.st_size <= 8_000_000 or want_name
            if not (want_name or want_hash or want_content):
                continue
            raw = None
            if want_content and st.st_size <= 8_000_000:
                try:
                    raw = p.read_bytes()
                except Exception:
                    errors += 1
                    continue
            hashed += 1 if want_hash else 0
            rec = record_file(p, hashed=want_hash or want_name, raw=raw)
            if rec.get("exact_json_sha"):
                sha_hits.append(rec)
            if rec.get("contains_fp_root"):
                root_hits.append(rec)
            if want_name:
                name_hits.append(rec)
    known_status = []
    for p in KNOWN:
        known_status.append({"path": str(p), "exists": p.exists(), "is_dir": p.is_dir() if p.exists() else False})
        if p.is_file():
            rec = record_file(p, hashed=True, raw=None)
            name_hits.append(rec)
            if rec.get("exact_json_sha"):
                sha_hits.append(rec)
            if rec.get("contains_fp_root"):
                root_hits.append(rec)
        elif p.is_dir():
            try:
                for child in sorted(p.iterdir())[:80]:
                    if child.is_file() and (basename_hit(child.name) or child.suffix == ".json"):
                        rec = record_file(child, hashed=True, raw=None)
                        name_hits.append(rec)
                        if rec.get("exact_json_sha"):
                            sha_hits.append(rec)
                        if rec.get("contains_fp_root"):
                            root_hits.append(rec)
            except Exception:
                pass
    return {
        "document": "FINGERPRINT_FILESYSTEM_SEARCH",
        "skip_dirs": sorted(SKIP_DIRS),
        "files_seen": scanned,
        "files_hashed_or_read": hashed,
        "read_errors": errors,
        "known_locations": known_status,
        "sha_match_files": sha_hits,
        "fp_root_files": root_hits,
        "basename_fingerprint_files": name_hits[:80],
        "accepted_fp_root": FP_ROOT,
        "accepted_fp_json_sha256": FP_JSON_SHA,
    }


def contradiction_candidates(search: Dict[str, Any]) -> List[Dict[str, Any]]:
    bad: List[Dict[str, Any]] = []
    seen = set()
    for rec in (search.get("basename_fingerprint_files") or []) + (search.get("sha_match_files") or []) + (search.get("fp_root_files") or []):
        path = rec.get("absolute_path")
        if path in seen:
            continue
        seen.add(path)
        preview = rec.get("preview_utf8_4kib") or ""
        sha = rec.get("sha256")
        has_root = rec.get("contains_fp_root")
        if sha == FP_JSON_SHA or has_root:
            continue
        if not rec.get("basename_fingerprint") and not path.endswith(".json"):
            continue
        hexes = HEX64.findall(preview)
        other = [h.lower() for h in hexes if h.lower() != FP_ROOT]
        semantic = any(k in preview.lower() for k in ("fingerprint_root", "runtime_fingerprint", "fingerprint"))
        if other and semantic and not has_root:
            bad.append({"path": path, "sha256": sha, "other_hex64": other[:8], "reason": "fingerprint-like artifact without accepted root"})
    return bad


def classify_and_report(classification: str, extra: Dict[str, Any]) -> None:
    diag_id = os.environ.get("OTT_DIAGNOSTIC_ID", "")
    if classification == "B_FINGERPRINT_NOT_EMBEDDED_AUDITOR_DECISION_REQUIRED":
        gen2 = "UNCONSUMED_PENDING_AUDITOR_DECISION"
    elif classification == "A_EXISTING_IMMUTABLE_FINGERPRINT_RELOCATION":
        gen2 = "UNCONSUMED"
    else:
        gen2 = "UNCONSUMED_PENDING_AUDITOR_DECISION"
    doc = {
        "document": "FINGERPRINT_CLASSIFICATION",
        "diagnostic_id": diag_id,
        "RUNTIME_FINGERPRINT_CLASSIFICATION": classification,
        "RUN_AUTHORIZATION_CONSUMED": "NO",
        "START_STAGE_A": "ABSENT",
        "SCIENTIFIC_OBSERVATIONS": 0,
        "STAGE_A_EXECUTION": "NO",
        "DOI_SEEDS_DERIVED": 0,
        "IPC_SPLIT_DERIVED": 0,
        "GENERATION_2_RUN_AUTHORIZATION_SHA256": AUTH_SHA,
        "GENERATION_2_RUN_AUTHORIZATION_STATUS": gen2,
        "parent_stage_a_run_id": PARENT_STAGE_A_RUN_ID,
        "github_parent_run_id": GITHUB_PARENT_RUN_ID,
        **extra,
    }
    write_json("FINGERPRINT_CLASSIFICATION.json", doc)
    write_text("FINGERPRINT_CLASSIFICATION.txt", classification + "\n")
    extra_txt = json.dumps(extra, indent=2, sort_keys=True, default=str)
    report = f"""# OTT v0.5.6 — RUNTIME FINGERPRINT PRESTART DIAGNOSTIC

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: RUNTIME_FINGERPRINT_PRESTART_DIAGNOSTIC
RUN_ID: {diag_id}
MESSAGE_ID: {diag_id}-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: {utc_now()}
AGENT: Cursor/GitHub Actions runtime-fingerprint PRESTART diagnostic
PARENT_STAGE_A_RUN_ID: {PARENT_STAGE_A_RUN_ID}
PARENT_GITHUB_RUN_ID: {GITHUB_PARENT_RUN_ID}
GENERATION_2_RUN_AUTHORIZATION_SHA256: {AUTH_SHA}
BASE_RUNTIME_DIGEST: {RUNTIME_DIGEST}
END_OTT_REPORT_SIGNATURE

```
RUNTIME_FINGERPRINT_PRESTART_DIAGNOSTIC = PASS

RUNTIME_FINGERPRINT_CLASSIFICATION =
{classification}

GENERATION_2_RUN_AUTHORIZATION_STATUS =
{gen2}

RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
STAGE_A_EXECUTION = NO
DOI_SEEDS_DERIVED = 0
IPC_SPLIT_DERIVED = 0
```

{extra_txt}
"""
    write_text("FINAL_REPORT.md", report)
    write_text("DIAGNOSTIC_ID.txt", diag_id + "\n")
    print(f"RUNTIME_FINGERPRINT_CLASSIFICATION = {classification}", flush=True)


def main() -> int:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    write_text("RUN_AUTHORIZATION_CONSUMED.txt", "NO\n")
    write_text("START_STAGE_A.txt", "ABSENT\n")
    write_text("STAGE_A_EXECUTION.txt", "NO\n")
    write_text("SCIENTIFIC_OBSERVATIONS.txt", "0\n")
    write_text("DOI_SEEDS_DERIVED.txt", "0\n")
    write_text("IPC_SPLIT_DERIVED.txt", "0\n")
    try:
        if Path("/ott/run").exists() or Path("/workspace/ott-run").exists():
            raise Stop("STOP_RFP_PARENT_OCI_IDENTITY_FAILURE", {"detail": "ott-run must stay unused"})
        digest_env = os.environ.get("OTT_RUNTIME_DIGEST", RUNTIME_DIGEST)
        if digest_env != RUNTIME_DIGEST:
            raise Stop("STOP_RFP_PARENT_OCI_IDENTITY_FAILURE", {"digest_env": digest_env})
        locator = _fingerprint_check()
        write_json(
            "CURRENT_LOCATOR_REPRODUCTION.json",
            {
                "document": "CURRENT_LOCATOR_REPRODUCTION",
                "verbatim_from": "tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py:_fingerprint_check",
                "candidate_files": locator.get("candidate_files"),
                "candidate_files_all": locator.get("candidate_files_all"),
                "matched_json": locator.get("fingerprint_file_sha_match"),
                "matched_root": locator.get("fingerprint_root_seen_in"),
                "platform": locator.get("platform"),
            },
        )
        search = exhaustive_search()
        write_json("FINGERPRINT_FILESYSTEM_SEARCH.json", search)
        bad = contradiction_candidates(search)
        exact_sha_paths = [r["absolute_path"] for r in search.get("sha_match_files") or []]
        exact_root_paths = [r["absolute_path"] for r in search.get("fp_root_files") or []]
        locator_miss = locator.get("fingerprint_file_sha_match") is None and locator.get("fingerprint_root_seen_in") is None
        if bad and not exact_sha_paths and not exact_root_paths:
            classify_and_report(
                "C_RUNTIME_FINGERPRINT_CONTRADICTION",
                {"stop": "STOP_RFP_RUNTIME_FINGERPRINT_CONTRADICTION", "contradictions": bad},
            )
            return 2
        if bad and (exact_sha_paths or exact_root_paths):
            classify_and_report(
                "C_RUNTIME_FINGERPRINT_CONTRADICTION",
                {
                    "stop": "STOP_RFP_RUNTIME_FINGERPRINT_CONTRADICTION",
                    "detail": "accepted fingerprint present together with a non-identical fingerprint-like authority",
                    "contradictions": bad,
                    "accepted_sha_paths": exact_sha_paths,
                    "accepted_root_paths": exact_root_paths,
                },
            )
            return 2
        if exact_sha_paths or exact_root_paths:
            if locator_miss:
                classify_and_report(
                    "A_EXISTING_IMMUTABLE_FINGERPRINT_RELOCATION",
                    {
                        "NEW_RUNTIME_BYTES": 0,
                        "SCIENTIFIC_SEMANTICS_DELTA": 0,
                        "OCI_MUTATION_REQUIRED": "NO",
                        "NEW_AUTHORIZATION_REQUIRED": "NO",
                        "canonical_sha_paths": exact_sha_paths,
                        "canonical_root_paths": exact_root_paths,
                        "locator_matched_json": locator.get("fingerprint_file_sha_match"),
                        "locator_matched_root": locator.get("fingerprint_root_seen_in"),
                    },
                )
                return 0
            classify_and_report(
                "C_RUNTIME_FINGERPRINT_CONTRADICTION",
                {
                    "stop": "STOP_RFP_RUNTIME_FINGERPRINT_CONTRADICTION",
                    "detail": "accepted fingerprint is inside the current Stage-A locator search set; this contradicts parent STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE",
                    "canonical_sha_paths": exact_sha_paths,
                    "canonical_root_paths": exact_root_paths,
                    "locator_matched_json": locator.get("fingerprint_file_sha_match"),
                    "locator_matched_root": locator.get("fingerprint_root_seen_in"),
                },
            )
            return 2
        classify_and_report(
            "B_FINGERPRINT_NOT_EMBEDDED_AUDITOR_DECISION_REQUIRED",
            {
                "oci_digest_identity": "PASS",
                "exact_json_sha_found": False,
                "exact_fp_root_found": False,
                "contradictory_fingerprint": False,
                "locator_matched_json": locator.get("fingerprint_file_sha_match"),
                "locator_matched_root": locator.get("fingerprint_root_seen_in"),
                "note": "Stage-A requirement 'fingerprint root must be found in image filesystem' is not satisfied by the frozen OCI layout. This does not authorize removing or weakening that gate.",
            },
        )
        return 0
    except Stop as e:
        classify_and_report("C_RUNTIME_FINGERPRINT_CONTRADICTION", {"stop": e.code, **e.extra})
        return 2
    except Exception as e:
        traceback.print_exc()
        classify_and_report(
            "C_RUNTIME_FINGERPRINT_CONTRADICTION",
            {"stop": "STOP_RFP_PARENT_OCI_IDENTITY_FAILURE", "error": f"{type(e).__name__}: {e}"},
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
