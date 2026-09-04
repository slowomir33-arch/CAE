#!/usr/bin/env python3
"""OTT v0.5.6 Stage-A external execution wrapper (post-publication glue).

This file is NOT part of PUBLIC_PROTOCOL_ROOT. It must not modify extracted
public-protocol bytes. Semantic authorities are the frozen ott_v056 modules
and the pinned CAE / Lilotane / IPC trees inside the immutable runtime image.

Do not use Harness.stage_a_cae() as the decisive scientific surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen identities (must match the Stage-A packet / P2B authorization)
# ---------------------------------------------------------------------------
PROTOCOL_VERSION = "v0.5.6"
RUN_ID_DEFAULT = "OTT-v0.5.6-SCA-20260904T061758Z-AF83E092"
PREV_STOP = "OTT-v0.5.6-SCA-20260904T061127Z-40797FC6"
VERSION_DOI = "10.5281/zenodo.22293061"
CONCEPT_DOI = "10.5281/zenodo.22293060"
SENTINEL_DOI = "10.0000/OTT-V0.5.6-TEST-DO-NOT-PUBLISH"
ZIP_NAME = "OTT_v0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_20260904T043759Z_74EB9712.zip"
ZIP_BYTES = 58243
ZIP_SHA256 = "41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f"
PROTOCOL_ROOT = "b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516"
AUTH_SHA256 = "4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358"
RUNTIME_REF = (
    "ghcr.io/slowomir33-arch/cae-ott-v055-runtime@"
    "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
)
RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
FP_ROOT = "166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271"
FP_JSON_SHA = "8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd"
CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
LILOTANE_COMMIT = "0a58c299c7d85034661f795dfe7b10ad64f547d3"
PANDAPI_COMMIT = "95bbe291c5bdb9fb517c1ad55f5136d45450c644"
IPC_COMMIT = "9e313248244a0a13302ae262f42ef446f43e4182"
NUMPY_VERSION = "2.2.0"
RECORD_ID = 22293061
WALL_LIMIT_S = 20.0
RSS_LIMIT = 4294967296
AUTH_SCOPE = "SCIENTIFIC_CHALLENGE_STAGE_A_RAW_EXECUTION_ONLY"

PAIRS: List[Tuple[str, str]] = [
    ("logic_circuit", "valid"),
    ("logic_circuit", "fail"),
    ("logic_circuit", "inv_internal"),
    ("tracr", "valid"),
    ("tracr", "fail"),
    ("grn", "valid"),
    ("grn", "wrong_map"),
    ("grn", "wrong_high_level_model"),
    ("cpu_6502", "valid_gate_isa"),
    ("cpu_6502", "valid_transistor_gate"),
    ("cpu_6502", "valid_transistor_isa"),
    ("cpu_6502", "broken_gate_isa"),
    ("cpu_6502", "broken_transistor_gate"),
    ("cpu_6502", "broken_transistor_isa"),
]


class StopError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dumps_scientific(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise StopError("STOP_STAGE_A_OUTPUT_WRITE_FAILURE", f"refusing overwrite of {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_new_text(path: Path, text: str) -> None:
    write_new(path, text.encode("utf-8"))


def exclusive_create(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as e:
        raise StopError("STOP_STAGE_A_OUTPUT_WRITE_FAILURE", f"exclusive create failed: {path}") from e
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pyify(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    if isinstance(obj, float):
        return obj
    if isinstance(obj, dict):
        return {str(k): pyify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [pyify(v) for v in obj]
    try:
        import numpy as np

        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return pyify(obj.tolist())
    except Exception:
        pass
    return obj


def record_stop(receipts: Path, code: str, detail: str, *, consumed: bool) -> None:
    receipts.mkdir(parents=True, exist_ok=True)
    (receipts / "PRESTART_STOP_CODE.txt").write_text(code + "\n", encoding="utf-8")
    payload = {
        "code": code,
        "detail": detail,
        "consumed": consumed,
        "timestamp_utc": utc_now(),
        "traceback": traceback.format_exc(),
    }
    dest = receipts / ("POSTSTART_STOP.json" if consumed else "PRESTART_STOP.json")
    dest.write_text(dumps_scientific(payload) + "\n", encoding="utf-8")
    (receipts / "FINAL_VERDICT.txt").write_text(code + "\n", encoding="utf-8")
    print(f"STOP {code}: {detail}", file=sys.stderr)


def git_head(path: Path) -> Optional[str]:
    if not (path / ".git").exists() and not (path / "HEAD").exists():
        # still try git -C
        pass
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out if re.fullmatch(r"[0-9a-f]{40}", out) else None
    except Exception:
        return None


def find_git_root_with_head(expected: str, roots: Sequence[Path]) -> Tuple[Optional[Path], Optional[str]]:
    for root in roots:
        if not root.exists():
            continue
        # search a few levels
        candidates = [root]
        try:
            for p in root.rglob(".git"):
                if p.is_dir() or p.is_file():
                    candidates.append(p.parent)
                if len(candidates) > 40:
                    break
        except Exception:
            pass
        for c in candidates:
            h = git_head(c)
            if h == expected:
                return c, h
        h = git_head(root)
        if h:
            return root, h
    return None, None


# ===========================================================================
# Host phases (stdlib only; never import ott_v056 / numpy 2.2 here)
# ===========================================================================
def phase_host_public_protocol(args: argparse.Namespace) -> None:
    receipts = Path(args.receipts_dir)
    protocol_dir = Path(args.protocol_dir)
    auth_path = Path(args.auth_path)
    receipts.mkdir(parents=True, exist_ok=True)

    rec_url = f"https://zenodo.org/api/records/{RECORD_ID}"
    req = urllib.request.Request(rec_url, headers={"User-Agent": "OTT-v0.5.6-stage-a"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        rec_raw = resp.read()
        rec_status = resp.status
    write_new(receipts / "ZENODO_RECORD.json", rec_raw)
    rec = json.loads(rec_raw.decode("utf-8"))
    isopen = rec.get("metadata", {}).get("access_right") or rec.get("access", {}).get("record")
    published = rec.get("metadata", {}).get("doi") == VERSION_DOI or rec.get("doi") == VERSION_DOI
    ident = rec.get("id")
    if rec_status != 200 or ident != RECORD_ID:
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"record GET status={rec_status} id={ident}")
    # published / open
    hits = json.dumps(rec).lower()
    if "22293061" not in hits:
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", "record payload missing 22293061")

    zip_url = (
        f"https://zenodo.org/records/{RECORD_ID}/files/{ZIP_NAME}?download=1"
    )
    zpath = receipts / ZIP_NAME
    req = urllib.request.Request(zip_url, headers={"User-Agent": "OTT-v0.5.6-stage-a"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        zbytes = resp.read()
    write_new(zpath, zbytes)
    if len(zbytes) != ZIP_BYTES:
        raise StopError(
            "STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE",
            f"zip bytes {len(zbytes)} != {ZIP_BYTES}",
        )
    zsha = sha256_bytes(zbytes)
    if zsha != ZIP_SHA256:
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"zip sha {zsha}")
    if protocol_dir.exists():
        shutil.rmtree(protocol_dir)
    protocol_dir.mkdir(parents=True)
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(protocol_dir)
    # zip may contain a single top-level directory
    entries = [p for p in protocol_dir.iterdir()]
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for child in inner.iterdir():
            shutil.move(str(child), str(protocol_dir / child.name))
        inner.rmdir()

    man_path = protocol_dir / "CANDIDATE_MANIFEST.sha256"
    if not man_path.is_file():
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", "missing CANDIDATE_MANIFEST.sha256")
    man_bytes = man_path.read_bytes()
    root = sha256_bytes(man_bytes)
    if root != PROTOCOL_ROOT:
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"root {root}")
    rows = [ln for ln in man_bytes.decode("utf-8").splitlines() if ln.strip()]
    if len(rows) != 35:
        raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"manifest rows {len(rows)}")
    for ln in rows:
        parts = ln.split()
        if len(parts) < 2:
            raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"bad manifest line {ln!r}")
        digest, rel = parts[0], parts[-1]
        fp = protocol_dir / rel
        if not fp.is_file():
            raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"missing {rel}")
        got = sha256_file(fp)
        if got != digest:
            raise StopError("STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE", f"{rel} sha {got}")

    auth_raw = auth_path.read_bytes()
    auth_sha = sha256_bytes(auth_raw)
    if auth_sha != AUTH_SHA256:
        raise StopError("STOP_STAGE_A_RUN_AUTHORIZATION_MISMATCH", f"auth sha {auth_sha}")
    auth = json.loads(auth_raw.decode("utf-8"))
    required = {
        "authorization_scope": AUTH_SCOPE,
        "public_v0_5_6_doi": VERSION_DOI,
        "public_protocol_zip_sha256": ZIP_SHA256,
        "public_protocol_root_sha256": PROTOCOL_ROOT,
        "runtime_digest": RUNTIME_DIGEST,
        "consumed": False,
        "start_stage_a": "ABSENT",
    }
    for k, v in required.items():
        if auth.get(k) != v:
            raise StopError("STOP_STAGE_A_RUN_AUTHORIZATION_MISMATCH", f"{k}={auth.get(k)!r}")
    if CONCEPT_DOI in auth_raw.decode("utf-8"):
        raise StopError("STOP_STAGE_A_RUN_AUTHORIZATION_MISMATCH", "concept DOI present in authorization")

    shutil.copy2(auth_path, receipts / "RUN_AUTHORIZATION.json")
    ident_doc = {
        "PUBLIC_PROTOCOL_BYTE_IDENTITY": "PASS",
        "zip_bytes": ZIP_BYTES,
        "zip_sha256": zsha,
        "public_protocol_root_sha256": root,
        "manifest_rows": 35,
        "zenodo_record_http": rec_status,
        "RUN_AUTHORIZATION_IDENTITY": "PASS",
        "RUN_AUTHORIZATION_SHA256": auth_sha,
        "RUN_AUTHORIZATION_CONSUMED": "NO",
        "START_STAGE_A": "ABSENT",
        "concept_doi_in_authorization": False,
        "access_field": isopen,
        "published_doi_seen": published,
    }
    write_new_text(receipts / "PUBLIC_PROTOCOL_BYTE_IDENTITY.json", dumps_scientific(ident_doc) + "\n")
    write_new_text(receipts / "RUN_AUTHORIZATION_VERIFICATION.json", dumps_scientific({
        "sha256": auth_sha,
        "required": required,
        "PASS": True,
    }) + "\n")
    print("HOST_PUBLIC_PROTOCOL PASS")


def phase_host_start(args: argparse.Namespace) -> None:
    receipts = Path(args.receipts_dir)
    run_dir = Path(args.run_dir)
    auth_path = Path(args.auth_path)
    wrapper = Path(args.wrapper_path)
    ready = receipts / "PRESTART_STAGE_A_READY.json"
    if not ready.is_file():
        raise StopError("STOP_STAGE_A_OUTPUT_PATH_NOT_CLEAN", "PRESTART_STAGE_A_READY.json missing")
    ready_obj = json.loads(ready.read_text(encoding="utf-8"))
    if ready_obj.get("READY_TO_START_STAGE_A") != "YES":
        raise StopError("STOP_STAGE_A_OUTPUT_PATH_NOT_CLEAN", "not ready")
    if run_dir.exists():
        raise StopError("STOP_STAGE_A_OUTPUT_PATH_NOT_CLEAN", "run dir exists before START")
    run_dir.mkdir(parents=True, exist_ok=False)
    start_ts = utc_now()
    doc = {
        "document": "START_STAGE_A",
        "protocol_version": PROTOCOL_VERSION,
        "run_id": args.run_id,
        "start_timestamp_utc": start_ts,
        "public_v0_5_6_doi": VERSION_DOI,
        "concept_doi": CONCEPT_DOI,
        "concept_doi_used_for_scientific_hashing": False,
        "public_protocol_zip_sha256": ZIP_SHA256,
        "public_protocol_root_sha256": PROTOCOL_ROOT,
        "runtime_digest": RUNTIME_DIGEST,
        "run_authorization_sha256": AUTH_SHA256,
        "output_directory": str(run_dir.resolve()),
        "authorization_consumed": True,
        "previous_prestart_stop_run_id": PREV_STOP,
        "execution_environment": "GitHub Actions ubuntu-latest linux/X64",
        "prestart_ready_sha256": sha256_file(ready),
        "wrapper_sha256": sha256_file(wrapper),
    }
    raw = (dumps_scientific(doc) + "\n").encode("utf-8")
    exclusive_create(run_dir / "START_STAGE_A.json", raw)
    start_sha = sha256_bytes(raw)
    exclusive_create(run_dir / "START_STAGE_A.sha256", (start_sha + "\n").encode("ascii"))
    cons = {
        "document": "RUN_AUTHORIZATION_CONSUMPTION",
        "run_id": args.run_id,
        "consumed": True,
        "start_stage_a": "PRESENT",
        "start_stage_a_sha256": start_sha,
        "run_authorization_sha256": AUTH_SHA256,
        "original_authorization_modified": False,
        "consumption_timestamp_utc": start_ts,
        "authorization_scope": AUTH_SCOPE,
    }
    exclusive_create(run_dir / "RUN_AUTHORIZATION_CONSUMPTION.json", (dumps_scientific(cons) + "\n").encode("utf-8"))
    # copy original authorization bytes unchanged
    exclusive_create(run_dir / "RUN_AUTHORIZATION.json", auth_path.read_bytes())
    exclusive_create(run_dir / "stage_a_executor_v0.5.6.py", wrapper.read_bytes())
    exclusive_create(run_dir / "WRAPPER_SHA256.txt", (sha256_file(wrapper) + "\n").encode("ascii"))
    exclusive_create(run_dir / "incident_ledger.jsonl", b"")
    shutil.copy2(run_dir / "START_STAGE_A.json", receipts / "START_STAGE_A.json")
    shutil.copy2(run_dir / "START_STAGE_A.sha256", receipts / "START_STAGE_A.sha256")
    shutil.copy2(run_dir / "RUN_AUTHORIZATION_CONSUMPTION.json", receipts / "RUN_AUTHORIZATION_CONSUMPTION.json")
    print(f"START_STAGE_A sha256={start_sha}")


def phase_host_package(args: argparse.Namespace) -> None:
    receipts = Path(args.receipts_dir)
    run_dir = Path(args.run_dir)
    zip_dir = Path(args.zip_dir)
    zip_dir.mkdir(parents=True, exist_ok=True)
    utc = args.run_id.split("-SCA-")[-1].rsplit("-", 1)[0]
    run8 = args.run_id.rsplit("-", 1)[-1]
    zname = f"OTT_v0.5.6_STAGE_A_RAW_EVIDENCE_{utc}_{run8}.zip"
    zpath = zip_dir / zname
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for base, prefix in ((receipts, "gha-receipts"), (run_dir, "ott-run")):
            if not base.exists():
                continue
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    # never pack credentials
                    if p.name in {".dockerconfigjson", "config.json"} and "docker" in str(p).lower():
                        continue
                    zf.write(p, f"{prefix}/{p.relative_to(base).as_posix()}")
    zsha = sha256_file(zpath)
    write_new_text(zip_dir / "INNER_ZIP_SHA256.txt", zsha + "\n") if not (zip_dir / "INNER_ZIP_SHA256.txt").exists() else (zip_dir / "INNER_ZIP_SHA256.txt").write_text(zsha + "\n")
    meta = {
        "inner_zip": zname,
        "inner_zip_bytes": zpath.stat().st_size,
        "inner_zip_sha256": zsha,
        "run_id": args.run_id,
        "verdict": args.verdict,
        "start_present": args.start_present,
        "consumed": args.consumed,
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "github_sha": os.environ.get("GITHUB_SHA"),
    }
    (zip_dir / "INNER_ZIP_IDENTITY.json").write_text(dumps_scientific(meta) + "\n", encoding="utf-8")
    (receipts / "INNER_ZIP_SHA256.txt").write_text(zsha + "\n", encoding="utf-8")
    print(f"INNER_ZIP {zname} sha256={zsha} bytes={zpath.stat().st_size}")


# ===========================================================================
# Container PRESTART
# ===========================================================================
def _add_protocol_src(protocol_dir: Path) -> None:
    src = str(protocol_dir / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _ensure_cae_workspace() -> Path:
    ws = Path("/workspace")
    cae_alt = Path("/opt/ott/sources/CAE")
    if (ws / "systems" / "10_cpu_6502.py").is_file():
        return ws
    if (cae_alt / "systems" / "10_cpu_6502.py").is_file():
        # tests hardcode /workspace/systems/10_cpu_6502.py
        if ws.exists() and not ws.is_symlink() and any(ws.iterdir()):
            raise StopError(
                "STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE",
                "/workspace exists but is not pinned CAE; refusing to clobber",
            )
        if not ws.exists() or ws.is_symlink() or not any(ws.iterdir()):
            if ws.exists() and not ws.is_symlink():
                ws.rmdir()
            os.symlink(str(cae_alt), str(ws), target_is_directory=True)
        return ws
    raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", "pinned CAE tree not found")


def _load_system(filename: str, name: str) -> Any:
    ws = Path("/workspace")
    test_dir = ws / "test"
    if str(ws) not in sys.path:
        sys.path.insert(0, str(ws))
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))
    from utils import load_system

    return load_system(filename, name)


def _discover_lilotane() -> Dict[str, Any]:
    found: List[Path] = []
    which = shutil.which("lilotane")
    if which:
        found.append(Path(which))
    for root in (Path("/opt/ott/bin"), Path("/opt/ott"), Path("/usr/local/bin")):
        if not root.exists():
            continue
        try:
            if root.is_file():
                continue
            for p in root.rglob("lilotane"):
                if p.is_file() and os.access(p, os.X_OK):
                    found.append(p)
                if len(found) > 20:
                    break
        except Exception:
            pass
    # unique by resolve
    uniq = []
    seen = set()
    for p in found:
        r = str(p.resolve())
        if r not in seen:
            seen.add(r)
            uniq.append(p.resolve())
    if not uniq:
        raise StopError("STOP_STAGE_A_LILOTANE_INVOCATION_AMBIGUOUS", "lilotane binary not found")
    # Prefer PATH /opt/ott/bin
    binary = uniq[0]
    for p in uniq:
        if "/opt/ott/bin/" in str(p) or p.name == "lilotane":
            binary = p
            break
    help_proc = subprocess.run(
        [str(binary), "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    help_txt = (help_proc.stdout or "") + "\n" + (help_proc.stderr or "")
    # Unique invocation: unmodified binary + two positional HDDL files.
    # Optional flags with defaults are not a second mode.
    lower = help_txt.lower()
    positional_ok = (
        "domain" in lower and "problem" in lower
    ) or bool(re.search(r"<\s*domain", help_txt, re.I)) or bool(re.search(r"domainFile|domain\.hddl", help_txt, re.I))
    # Mandatory mode flags without frozen selector → ambiguous
    mandatory_mode = bool(re.search(r"required.*(--sat|--bdd|--planner-mode|-m )", help_txt, re.I))
    if (not positional_ok) or mandatory_mode:
        raise StopError(
            "STOP_STAGE_A_LILOTANE_INVOCATION_AMBIGUOUS",
            "cannot mechanically unique-ify lilotane argv from --help",
        )
    # If several distinct binaries with different hashes, still OK if argv pattern is unique.
    hashes = sorted({sha256_file(p) for p in uniq})
    return {
        "binary": str(binary),
        "binary_sha256": sha256_file(binary),
        "n_binaries_seen": len(uniq),
        "binary_hashes": hashes,
        "help_exit": help_proc.returncode,
        "help_sha256": sha256_bytes(help_txt.encode("utf-8", errors="replace")),
        "argv_template": [str(binary), "<domain.hddl>", "<problem.hddl>"],
        "extra_flags": [],
        "help_text": help_txt[:8000],
    }


def _locate_ipc(protocol_dir: Path) -> Dict[str, Any]:
    man = json.loads((protocol_dir / "protocol" / "IPC_ELIGIBLE_PROBLEM_MANIFEST_v0.5.6.json").read_text())
    eligible = man["eligible"]
    if len(eligible) != 120:
        raise StopError("STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS", f"eligible {len(eligible)}")
    bases = [
        Path("/opt/ott/sources/ipc2020-domains"),
        Path("/opt/ott/sources/panda-planner-dev/ipc2020-domains"),
        Path("/opt/ott/ipc2020-domains"),
        Path("/workspace/ipc2020-domains"),
    ]
    domain_base = "total-order"
    resolved_base = None
    for b in bases:
        probe = b / domain_base / "Rover-GTOHP" / "p01.hddl"
        if probe.is_file():
            resolved_base = b
            break
        probe2 = b / "total-order" / "Rover-GTOHP" / "p01.hddl"
        if probe2.is_file():
            resolved_base = b
            break
    if resolved_base is None:
        # last-ditch search
        for root in (Path("/opt/ott"), Path("/")):
            try:
                hits = list(root.glob("**/Rover-GTOHP/p01.hddl"))[:5]
            except Exception:
                hits = []
            if hits:
                resolved_base = hits[0].parent.parent.parent
                if resolved_base.name == "total-order":
                    resolved_base = resolved_base.parent
                break
    if resolved_base is None:
        raise StopError("STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS", "IPC tree not found")
    rows = []
    for item in eligible:
        domain = item["domain_id"]
        rel = item["canonical_relative_path"]
        companion = item["companion_domain_path"]
        problem = resolved_base / domain_base / domain / rel
        domain_file = resolved_base / domain_base / companion
        if not problem.is_file():
            raise StopError("STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS", f"missing problem {problem}")
        if not domain_file.is_file():
            raise StopError("STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS", f"missing domain {domain_file}")
        got = sha256_file(problem)
        if got != item["file_sha256"]:
            raise StopError(
                "STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS",
                f"sha mismatch {domain}/{rel}",
            )
        rows.append({
            "domain_id": domain,
            "canonical_relative_path": rel,
            "companion_domain_path": companion,
            "problem_abs": str(problem),
            "domain_abs": str(domain_file),
            "file_sha256": got,
        })
    from ott_v056.ipc_official import REQUIRED_COUNTS, counts_by_domain, d21_verdict

    obs = counts_by_domain(eligible)
    if d21_verdict(obs) != "PASS" or obs != REQUIRED_COUNTS:
        raise StopError("STOP_STAGE_A_BASELINE_SCHEDULING_AMBIGUOUS", f"counts {obs}")
    return {
        "ipc_root": str(resolved_base),
        "domain_base": domain_base,
        "n": len(rows),
        "counts": obs,
        "rows": rows,
        "ipc_head": git_head(resolved_base) or git_head(resolved_base.parent),
    }


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
    # uname / platform
    uname = os.uname()
    plat = {
        "sysname": uname.sysname,
        "machine": uname.machine,
        "release": uname.release,
    }
    if uname.sysname != "Linux" or uname.machine not in {"x86_64", "amd64"}:
        raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"platform {plat}")
    return {
        "platform": plat,
        "fingerprint_file_sha_match": matched_json,
        "fingerprint_root_seen_in": matched_root,
        "fingerprint_root_required": FP_ROOT,
        "fingerprint_json_sha_required": FP_JSON_SHA,
        "candidate_files": [str(p) for p in hits[:20]],
    }


def _run_public_tests(protocol_dir: Path, receipts: Path) -> Dict[str, Any]:
    pytest_deps = receipts / "pytest-deps"
    env = os.environ.copy()
    pp = [
        str(pytest_deps),
        str(protocol_dir / "src"),
        "/workspace",
        "/workspace/test",
    ]
    env["PYTHONPATH"] = os.pathsep.join(pp + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(protocol_dir / "tests"),
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(protocol_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=1800,
    )
    log = proc.stdout or ""
    write_new_text(receipts / "PUBLIC_TESTS.log", log)
    # expected 48 passed
    m = re.search(r"(\d+) passed", log)
    npass = int(m.group(1)) if m else -1
    if proc.returncode != 0 or npass < 48:
        raise StopError("STOP_STAGE_A_PRESTART_TEST_FAILURE", f"rc={proc.returncode} passed={npass}")
    if SENTINEL_DOI not in (protocol_dir / "src" / "ott_v056" / "__init__.py").read_text():
        raise StopError("STOP_STAGE_A_PRESTART_TEST_FAILURE", "sentinel DOI missing from package")
    # never substitute real DOI into tests — we did not
    return {"passed": npass, "returncode": proc.returncode, "PASS": True}


def _wrapper_conformance(protocol_dir: Path, receipts: Path) -> Dict[str, Any]:
    _add_protocol_src(protocol_dir)
    import numpy as np
    from ott_v056 import SENTINEL_DOI as SDOI
    from ott_v056.canonical import track_a_seed
    from ott_v056.cae_raw import execute_paired_raw, make_sampler, evaluate_probe  # sentinel-only
    from ott_v056.grounding import ground_intervention_spec
    from ott_v056.output import dumps_scientific as ds, jsonl_line
    from ott_v056.rng import (
        RUNTIME_NUMPY_VERSION,
        digest_to_entropy_words,
        first_draws,
        generators_for_probe,
        spawn_key_list,
        spawn_probe_sequences,
        probe_stream_sequences,
        require_runtime_numpy,
    )
    from ott_v056.v_metric import (
        GRN_ATOL,
        InfrastructureFailure,
        extract_frozen_vector,
        grn_equal,
        probe_match,
    )
    from causal_abstraction.sampling import BottomUpSampler, TopDownSampler

    require_runtime_numpy(NUMPY_VERSION)
    assert np.__version__ == RUNTIME_NUMPY_VERSION == NUMPY_VERSION

    # 1. sentinel seed preimages
    digest, pre = track_a_seed(SDOI, "logic_circuit", "valid", 0)
    vec = json.loads((protocol_dir / "tests" / "test_vectors.json").read_text())
    assert digest.hex() == vec["track_a_seed"]["sha256"]
    assert pre.hex() == vec["track_a_seed"]["preimage_hex"]
    assert CAE_COMMIT.encode("ascii") in pre
    assert VERSION_DOI.encode("ascii") not in pre  # sentinel, not real DOI

    # 2. D19 vectors probes 0,1,127
    doc = json.loads((protocol_dir / "protocol" / "NUMPY_RNG_TEST_VECTORS_v0.5.6.json").read_text())
    d = bytes.fromhex(doc["replicate_sha256"])
    assert digest_to_entropy_words(d) == doc["entropy_words"]
    probes = spawn_probe_sequences(d)
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
        s, g, p = generators_for_probe(d, i)
        assert first_draws(s) == streams["SAMPLER"]["first_draws"]
        assert first_draws(g) == streams["GROUND"]["first_draws"]
        assert first_draws(p) == streams["PATH"]["first_draws"]

    # 3–6 path identity / no bottom-up / atomicity / GRN / UNMAPPED
    from ott_v056.cae_raw import evaluate_probe as _ev  # fixture only here

    builder, vm, _high = _logic_bundle()
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
    assert hv1 == hv2 and lv1 == lv2

    sampler = make_sampler("logic_circuit", vm)
    assert isinstance(sampler, TopDownSampler)
    assert not isinstance(sampler, BottomUpSampler)

    assert probe_match([1, 2], [1, 2], mode="exact") == 1
    assert probe_match([1, 2], [1, 3], mode="exact") == 0
    assert grn_equal(0.0, GRN_ATOL) is True
    assert grn_equal(float("nan"), float("nan")) is False
    try:
        extract_frozen_vector({"fz_tgt": [float("nan")]}, ["fz_tgt"])
        raise StopError("STOP_STAGE_A_WRAPPER_CONFORMANCE_FAILURE", "NaN did not STOP")
    except InfrastructureFailure:
        pass
    hv, hs = extract_frozen_vector({"Y": [1]}, ["Y"])
    lv, ls = extract_frozen_vector({"Y": ["UNMAPPED"]}, ["Y"], nonfinite_is_infrastructure=False)
    assert probe_match(hv, lv, mode="exact", high_status=hs, low_status=ls) == 0

    # 8. MSE/IIA/DCC not used — one sentinel evaluate_probe (NON_SCIENTIFIC)
    called = []

    def boom(*a, **k):
        called.append(1)
        raise AssertionError("scalar CAE metric used for V")

    import causal_abstraction.engine as engine_mod
    from causal_abstraction.metrics import MSEMetric
    from causal_abstraction.analytical_metrics import DCCMetric, IIAMetric

    engine_mod.EvaluationEngine._score_collected_results = boom  # type: ignore
    MSEMetric.measure = boom  # type: ignore
    IIAMetric.compute = boom  # type: ignore
    DCCMetric.compute = boom  # type: ignore
    s, g, p = generators_for_probe(digest, 0)
    rec = evaluate_probe(system="logic_circuit", builder=builder, sampler_rng=s, ground_rng=g, path_rng=p)
    assert rec["scalar_cae_metric"] is None
    assert rec["probe_match"] in (0, 1)
    assert called == []
    assert rec.get("NON_SCIENTIFIC_TEST_FIXTURE") == "YES"

    # 9. JSONL canonicalization
    line = jsonl_line({"b": 1, "a": 2}, fixture=True)
    assert line == ds({"NON_SCIENTIFIC_TEST_FIXTURE": "YES", "a": 2, "b": 1}) + "\n"
    assert " " not in line.strip()

    # 10. later stages impossible from this wrapper
    try:
        wrapper_refuse_later_stage("stage_b")
        raise StopError("STOP_STAGE_A_WRAPPER_CONFORMANCE_FAILURE", "stage_b did not refuse")
    except StopError as e:
        if e.code != "STOP_STAGE_A_UNAUTHORIZED_LATER_STAGE":
            raise

    return {
        "PASS": True,
        "sentinel_seed": digest.hex(),
        "d19_probes": ["0", "1", "127"],
        "path_identity": True,
        "bottom_up": False,
        "scalar_calls": 0,
    }


def wrapper_refuse_later_stage(name: str) -> None:
    raise StopError("STOP_STAGE_A_UNAUTHORIZED_LATER_STAGE", name)


def _logic_bundle():
    from causal_abstraction import EvaluationConfig, MicroVariableSchema
    from causal_abstraction.paths import DiagramBuilder

    lc = _load_system("01_logic_circuit.py", "logic_circuit_sys")
    gates, all_wires = lc.build_2bit_adder()
    schema = MicroVariableSchema.from_names(all_wires)
    low_level = lc.NetlistSimulator(gates, all_wires)
    cg, vm = lc.build_cg_and_vm(schema)
    high = lc.build_valid_high_level_model()
    builder = DiagramBuilder(high, low_level, vm, cg, EvaluationConfig(metric="hard"))
    return builder, vm, high


def phase_prestart(args: argparse.Namespace) -> None:
    receipts = Path(args.receipts_dir)
    protocol_dir = Path(args.protocol_dir)
    receipts.mkdir(parents=True, exist_ok=True)
    try:
        ws = _ensure_cae_workspace()
        import numpy as np

        if np.__version__ != NUMPY_VERSION:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"numpy {np.__version__}")
        fp = _fingerprint_check()
        cae_head = git_head(ws) or git_head(Path("/opt/ott/sources/CAE"))
        lilo_head = git_head(Path("/opt/ott/sources/Lilotane")) or git_head(Path("/opt/ott/sources/lilotane"))
        panda_head = git_head(Path("/opt/ott/sources/pandaPIparser"))
        # imports / bridges
        import causal_abstraction  # noqa: F401
        from causal_abstraction.paths import DiagramBuilder  # noqa: F401
        from causal_abstraction.sampling import TopDownSampler  # noqa: F401

        cpu = _load_system("10_cpu_6502.py", "cpu_6502_precheck")
        lib_isa = cpu._find_lib("libisa_bridge.so") or cpu._find_lib("isa_bridge.so")
        lib_gate = cpu._find_lib("libgate_bridge.so") or cpu._find_lib("gate_bridge.so")
        lib_tr = cpu._find_lib("libtransistor_bridge.so") or cpu._find_lib("transistor_bridge.so")
        if not (lib_isa and lib_gate and lib_tr):
            # try constructing simulators — they raise if missing
            try:
                cpu.ISASimulator()
                cpu.GateSimulator()
                native_ok = True
                native_detail = {"isa": True, "gate": True, "libs": [lib_isa, lib_gate, lib_tr]}
            except Exception as e:
                raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"native bridges: {e}") from e
        else:
            native_ok = True
            native_detail = {"isa": lib_isa, "gate": lib_gate, "transistor": lib_tr}

        lilo = _discover_lilotane()
        write_new_text(receipts / "LILOTANE_HELP.txt", lilo.get("help_text", ""))
        _add_protocol_src(protocol_dir)
        ipc = _locate_ipc(protocol_dir)
        write_new_text(receipts / "IPC_RESOLVED.json", dumps_scientific({
            k: ipc[k] for k in ("ipc_root", "domain_base", "n", "counts", "ipc_head")
        }) + "\n")
        write_new_text(receipts / "IPC_RESOLVED_ROWS.json", dumps_scientific({"rows": ipc["rows"]}) + "\n")

        if cae_head != CAE_COMMIT:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"CAE HEAD {cae_head}")
        if lilo_head not in (None, LILOTANE_COMMIT):
            # require exact if git metadata present
            if lilo_head != LILOTANE_COMMIT:
                raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"Lilotane HEAD {lilo_head}")
        # If HEAD missing, still require binary found (already). Prefer exact.
        if lilo_head != LILOTANE_COMMIT:
            # search more
            p, h = find_git_root_with_head(LILOTANE_COMMIT, [Path("/opt/ott")])
            lilo_head = h
        if lilo_head != LILOTANE_COMMIT:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"Lilotane HEAD {lilo_head}")
        if panda_head != PANDAPI_COMMIT:
            p, h = find_git_root_with_head(PANDAPI_COMMIT, [Path("/opt/ott")])
            panda_head = h
        if panda_head != PANDAPI_COMMIT:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"pandaPIparser HEAD {panda_head}")
        ipc_head = ipc.get("ipc_head")
        if ipc_head != IPC_COMMIT:
            p, h = find_git_root_with_head(IPC_COMMIT, [Path("/opt/ott"), Path(ipc["ipc_root"])])
            ipc_head = h
        if ipc_head != IPC_COMMIT:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"IPC HEAD {ipc_head}")

        if fp["fingerprint_root_seen_in"] is None and fp["fingerprint_file_sha_match"] is None:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", "fingerprint root not found in image")

        tests = _run_public_tests(protocol_dir, receipts)
        conf = _wrapper_conformance(protocol_dir, receipts)

        digest_env = os.environ.get("OTT_RUNTIME_DIGEST", RUNTIME_DIGEST)
        if digest_env != RUNTIME_DIGEST:
            raise StopError("STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE", f"digest env {digest_env}")

        runtime_doc = {
            "STAGE_A_RUNTIME_PRECHECK": "PASS",
            "platform": fp["platform"],
            "numpy": np.__version__,
            "cae_head": cae_head,
            "lilotane_head": lilo_head,
            "pandapi_head": panda_head,
            "ipc_head": ipc_head,
            "fingerprint": fp,
            "native_bridges": native_detail,
            "native_ok": native_ok,
            "lilotane": {k: v for k, v in lilo.items() if k != "help_text"},
            "workspace": str(ws),
        }
        write_new_text(receipts / "RUNTIME_PRECHECK.json", dumps_scientific(runtime_doc) + "\n")
        write_new_text(receipts / "PUBLIC_TESTS.json", dumps_scientific(tests) + "\n")
        write_new_text(receipts / "WRAPPER_CONFORMANCE.json", dumps_scientific(conf) + "\n")

        ready = {
            "document": "PRESTART_STAGE_A_READY",
            "run_id": args.run_id,
            "PUBLIC_PROTOCOL_BYTE_IDENTITY": "PASS",
            "RUN_AUTHORIZATION_IDENTITY": "PASS",
            "RUN_AUTHORIZATION_CONSUMED": "NO",
            "RUNTIME_PRECHECK": "PASS",
            "PUBLIC_TESTS": "PASS",
            "EXECUTION_WRAPPER_CONFORMANCE": "PASS",
            "LILOTANE_INVOCATION": "RESOLVED",
            "IPC_MANIFEST": "120_AND_PASS",
            "START_STAGE_A": "ABSENT",
            "SCIENTIFIC_OBSERVATIONS": 0,
            "READY_TO_START_STAGE_A": "YES",
            "wrapper_sha256": os.environ.get("OTT_WRAPPER_SHA256") or sha256_file(Path(args.wrapper_path)),
            "previous_prestart_stop_run_id": PREV_STOP,
            "timestamp_utc": utc_now(),
        }
        raw = (dumps_scientific(ready) + "\n").encode("utf-8")
        write_new(receipts / "PRESTART_STAGE_A_READY.json", raw)
        write_new_text(receipts / "PRESTART_STAGE_A_READY.sha256", sha256_bytes(raw) + "\n")
        print("PRESTART_STAGE_A_READY YES")
    except StopError as e:
        record_stop(receipts, e.code, e.detail, consumed=False)
        raise


# ===========================================================================
# Container SCIENCE (after exclusive START on the host)
# ===========================================================================
def _import_ott(protocol_dir: Path) -> None:
    _add_protocol_src(protocol_dir)


def _append_incident(run_dir: Path, rec: Dict[str, Any]) -> None:
    path = run_dir / "incident_ledger.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(dumps_scientific(pyify(rec)) + "\n")


def _build_pair(system: str, condition: str, cache: Dict[str, Any]) -> Any:
    from causal_abstraction import EvaluationConfig
    from causal_abstraction.paths import DiagramBuilder

    key = (system, condition)
    if key in cache:
        return cache[key]
    cfg = EvaluationConfig(metric="hard", n_jobs=1)
    if system == "logic_circuit":
        lc = _load_system("01_logic_circuit.py", "logic_circuit")
        from causal_abstraction import MicroVariableSchema

        gates, all_wires = lc.build_2bit_adder()
        schema = MicroVariableSchema.from_names(all_wires)
        low = lc.NetlistSimulator(gates, all_wires)
        cg, vm = lc.build_cg_and_vm(schema)
        high_fn = {
            "valid": lc.build_valid_high_level_model,
            "fail": lc.build_failing_high_level_model,
            "inv_internal": lc.build_inverted_internal_high_level_model,
        }.get(condition)
        if high_fn is None:
            raise StopError("STOP_STAGE_A_SYSTEM_CONSTRUCTION_AMBIGUOUS", condition)
        high = high_fn()
        builder = DiagramBuilder(high, low, vm, cg, cfg)
        cache[key] = builder
        return builder
    if system == "tracr":
        tr = cache.get("_tracr_mod") or _load_system("08_tracr.py", "tracr")
        cache["_tracr_mod"] = tr
        compiled = cache.get("_tracr_compiled")
        if compiled is None:
            compiled = tr.build_compiled_model()
            cache["_tracr_compiled"] = compiled
        low = tr.TracrLowLevelModel(compiled, tr.SEQ_LEN)
        _, cg, vm = tr._build_shared_maps()
        if condition == "valid":
            high = tr._build_high_level_model(tr._make_rank_equation)
        elif condition == "fail":
            high = tr._build_high_level_model(tr._make_failing_rank_equation)
        else:
            raise StopError("STOP_STAGE_A_SYSTEM_CONSTRUCTION_AMBIGUOUS", condition)
        builder = DiagramBuilder(high, low, vm, cg, cfg)
        cache[key] = builder
        return builder
    if system == "grn":
        import os as _os

        grn = _load_system("09_grn/grn.py", "grn")
        gin = "/workspace/systems/09_grn/regulatoryGraph.ginml"
        model = cache.get("_grn_model")
        if model is None:
            model = grn.SegmentPolarityModel.from_ginml(gin)
            cache["_grn_model"] = model
        schema = grn._base_schema()
        low = grn.SegmentPolarityLowLevelModel(model)
        if condition == "valid":
            cg, vm = grn.build_valid_cg_vm(schema)
            high = grn.build_valid_high_level_model()
        elif condition == "wrong_map":
            cg, vm = grn.build_wrong_cg_vm(schema)
            high = grn.build_valid_high_level_model()
        elif condition == "wrong_high_level_model":
            cg, vm = grn.build_valid_cg_vm(schema)
            high = grn.build_reversed_high_level_model()
        else:
            raise StopError("STOP_STAGE_A_SYSTEM_CONSTRUCTION_AMBIGUOUS", condition)
        builder = DiagramBuilder(high, low, vm, cg, cfg)
        cache[key] = builder
        return builder
    if system == "cpu_6502":
        cpu = cache.get("_cpu_mod") or _load_system("10_cpu_6502.py", "cpu_6502")
        cache["_cpu_mod"] = cpu
        schema = cache.get("_cpu_schema")
        if schema is None:
            schema = cpu.build_schema()
            cache["_cpu_schema"] = schema
            cache["_cpu_cg"] = cpu.build_cg(schema)
            cache["_cpu_vm"] = cpu.build_vm(cache["_cpu_cg"])
        cg, vm = cache["_cpu_cg"], cache["_cpu_vm"]
        if "transistor" in condition:
            base_low = cpu.TransistorSimulator()
        else:
            if "_cpu_gate" not in cache:
                cache["_cpu_gate"] = cpu.GateSimulator()
            base_low = cache["_cpu_gate"]
        low = cpu.StuckA7Simulator(base_low) if condition.startswith("broken_") else base_low
        if condition.endswith("_isa"):
            if "_cpu_isa" not in cache:
                cache["_cpu_isa"] = cpu.ISASimulator()
            high = cpu.build_isa_high_level_model(cache["_cpu_isa"])
        elif condition.endswith("_gate"):
            if "_cpu_gate" not in cache:
                cache["_cpu_gate"] = cpu.GateSimulator()
            high = cpu.build_gate_high_level_model(cache["_cpu_gate"])
        else:
            raise StopError("STOP_STAGE_A_SYSTEM_CONSTRUCTION_AMBIGUOUS", condition)
        builder = DiagramBuilder(high, low, vm, cg, cfg)
        cache[key] = builder
        return builder
    raise StopError("STOP_STAGE_A_SYSTEM_CONSTRUCTION_AMBIGUOUS", system)


def _make_sampler(system: str, builder: Any, cache: Dict[str, Any]) -> Any:
    from ott_v056.cae_raw import make_sampler
    from causal_abstraction.sampling import BottomUpSampler

    if system == "cpu_6502":
        cpu = cache.get("_cpu_mod") or _load_system("10_cpu_6502.py", "cpu_6502")
        cache["_cpu_mod"] = cpu
        sampler = cpu.InstructionSampler(builder.vm)
    else:
        sampler = make_sampler(system, builder.vm)
    if isinstance(sampler, BottomUpSampler) and type(sampler) is BottomUpSampler:
        raise StopError("STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE", "BottomUpSampler")
    return sampler


def _evaluate_scientific(system: str, builder: Any, sampler_rng, ground_rng, path_rng, cache) -> Dict[str, Any]:
    from ott_v056.cae_raw import complete_missing_roots, execute_paired_raw, resolve_vars
    from ott_v056.grounding import ground_intervention_spec
    from ott_v056.mapping import SYSTEMS, equality_mode, output_names
    from ott_v056.v_metric import extract_frozen_vector, probe_match

    cfg = SYSTEMS[system]
    sampler = _make_sampler(system, builder, cache)
    targets = resolve_vars(builder.high_level_model, cfg["intervention_domain"])
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
    spec = ground_intervention_spec(builder.vm, spec, ground_rng)
    high, low = execute_paired_raw(builder, spec, path_rng)
    names = output_names(system)
    mode = equality_mode(system)
    high_vec, high_st = extract_frozen_vector(high, names)
    low_vec, low_st = extract_frozen_vector(low, names)
    match = probe_match(high_vec, low_vec, mode=mode, high_status=high_st, low_status=low_st)
    return {
        "frozen_outputs": list(names),
        "high_vector": pyify(high_vec),
        "low_vector": pyify(low_vec),
        "high_status": list(high_st),
        "low_status": list(low_st),
        "probe_match": int(match),
        "scalar_cae_metric": None,
    }


def _rss_bytes(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    return int(parts[1]) * 1024
    except Exception:
        return 0
    return 0


def _run_lilotane(binary: str, domain: str, problem: str, work: Path) -> Dict[str, Any]:
    work.mkdir(parents=True, exist_ok=True)
    stdout_p = work / "stdout.bin"
    stderr_p = work / "stderr.bin"
    t0 = time.monotonic()
    with stdout_p.open("wb") as so, stderr_p.open("wb") as se:
        proc = subprocess.Popen(
            [binary, domain, problem],
            cwd=str(work),
            stdout=so,
            stderr=se,
        )
        peak = 0
        timed_out = False
        oom = False
        while True:
            rc = proc.poll()
            rss = _rss_bytes(proc.pid)
            if rss > peak:
                peak = rss
            elapsed = time.monotonic() - t0
            if rss > RSS_LIMIT:
                oom = True
                proc.kill()
                proc.wait()
                break
            if elapsed >= WALL_LIMIT_S:
                timed_out = True
                proc.kill()
                proc.wait()
                break
            if rc is not None:
                break
            time.sleep(0.02)
        wall = time.monotonic() - t0
        rc = proc.returncode
    stdout_b = stdout_p.stat().st_size
    stderr_b = stderr_p.stat().st_size
    # extra files produced
    extras = []
    for p in work.iterdir():
        if p.name not in {"stdout.bin", "stderr.bin"} and p.is_file():
            extras.append({"name": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    nonempty = (stdout_b > 0) or any(e["bytes"] > 0 for e in extras)
    if oom or timed_out:
        status = "UNSOLVED"
        err = "OOM" if oom else "TIMEOUT"
    elif rc != 0:
        status = "UNSOLVED"
        err = f"exit_{rc}"
    elif not nonempty:
        status = "UNSOLVED"
        err = "empty_output"
    else:
        status = "SOLVED"
        err = None
    return {
        "baseline_status": status,
        "wall_clock_s": wall,
        "peak_rss_bytes": peak,
        "exit_code": rc,
        "timeout_applied": timed_out,
        "oom_applied": oom,
        "plan_nonempty": nonempty,
        "error_class": err,
        "stdout_bytes": stdout_b,
        "stderr_bytes": stderr_b,
        "stdout_sha256": sha256_file(stdout_p),
        "stderr_sha256": sha256_file(stderr_p),
        "extra_files": extras,
        "raw_planner_output_sha256": sha256_file(stdout_p),
    }


def _seal(run_dir: Path) -> str:
    files = []
    for p in sorted(run_dir.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            files.append({
                "path": p.relative_to(run_dir).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    man = {
        "document": "STAGE_A_MANIFEST",
        "protocol_version": PROTOCOL_VERSION,
        "run_id": os.environ.get("OTT_RUN_ID", RUN_ID_DEFAULT),
        "files": files,
        "counters": {
            "candidate_selection_count": 0,
            "held_out_count": 0,
            "external_label_join_count": 0,
            "scoring_count": 0,
            "verdict_count": 0,
        },
    }
    raw = (dumps_scientific(man) + "\n").encode("utf-8")
    write_new(run_dir / "manifest.json", raw)
    root = sha256_bytes(raw)
    write_new_text(run_dir / "STAGE_A_EVIDENCE_ROOT_SHA256.txt", root + "\n")
    return root


def phase_science(args: argparse.Namespace) -> None:
    receipts = Path(args.receipts_dir)
    protocol_dir = Path(args.protocol_dir)
    run_dir = Path(args.run_dir)
    _import_ott(protocol_dir)
    from ott_v056.canonical import track_a_seed, track_b_split
    from ott_v056.grounding import GroundingRoundtripError
    from ott_v056.rng import generators_for_probe, require_runtime_numpy
    from ott_v056.v_metric import InfrastructureFailure

    require_runtime_numpy(NUMPY_VERSION)
    start = run_dir / "START_STAGE_A.json"
    if not start.is_file():
        raise StopError("STOP_STAGE_A_OUTPUT_PATH_NOT_CLEAN", "START missing in science phase")
    counters = {
        "candidate_selection_count": 0,
        "held_out_count": 0,
        "external_label_join_count": 0,
        "scoring_count": 0,
        "verdict_count": 0,
    }
    seed_seen: Dict[bytes, Tuple[str, str, int]] = {}
    units: set = set()
    cache: Dict[str, Any] = {}

    try:
        # --- seeds ---
        seed_rows = []
        for system, condition in PAIRS:
            for rep in range(32):
                digest, pre = track_a_seed(VERSION_DOI, system, condition, rep, cae_commit=CAE_COMMIT)
                if CONCEPT_DOI.encode("ascii") in pre:
                    raise StopError("STOP_STAGE_A_SEED_COLLISION", "concept DOI in preimage")
                if digest in seed_seen and seed_seen[digest] != (system, condition, rep):
                    raise StopError("STOP_STAGE_A_SEED_COLLISION", digest.hex())
                seed_seen[digest] = (system, condition, rep)
                seed_rows.append({
                    "system": system,
                    "condition": condition,
                    "replicate_index": rep,
                    "replicate_seed_sha256": digest.hex(),
                    "preimage_sha256": sha256_bytes(pre),
                    "preimage_hex": pre.hex(),
                })
        write_new_text(run_dir / "track_a_seeds.jsonl", "".join(dumps_scientific(r) + "\n" for r in seed_rows))
        if CONCEPT_DOI in (run_dir / "track_a_seeds.jsonl").read_text(encoding="utf-8"):
            raise StopError("STOP_STAGE_A_SEED_COLLISION", "concept DOI leaked into seeds file")

        # --- Track A ---
        out_a = run_dir / "stage_a_track_a.jsonl"
        n_a = 0
        with out_a.open("xb") as fh:
            for system, condition in PAIRS:
                print(f"TRACK_A begin {system}/{condition}", flush=True)
                try:
                    builder = _build_pair(system, condition, cache)
                except StopError:
                    raise
                except Exception as e:
                    raise StopError("STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE", f"build {system}/{condition}: {e}") from e
                for rep in range(32):
                    digest, _pre = track_a_seed(VERSION_DOI, system, condition, rep, cae_commit=CAE_COMMIT)
                    for probe in range(128):
                        uid = f"A|{system}|{condition}|{rep}|{probe}"
                        if uid in units:
                            raise StopError("STOP_STAGE_A_DUPLICATE_UNIT", uid)
                        units.add(uid)
                        t0 = time.monotonic()
                        try:
                            s, g, p = generators_for_probe(digest, probe)
                            payload = _evaluate_scientific(system, builder, s, g, p, cache)
                        except GroundingRoundtripError as e:
                            raise StopError("STOP_GROUNDING_ROUNDTRIP_FAILURE", str(e)) from e
                        except InfrastructureFailure as e:
                            msg = str(e)
                            if "non-finite" in msg:
                                raise StopError("STOP_STAGE_A_NONFINITE_MANDATORY_OUTPUT", msg) from e
                            raise StopError("STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE", msg) from e
                        except StopError:
                            raise
                        except Exception as e:
                            raise StopError("STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE", f"{uid}: {e}") from e
                        dt_ms = (time.monotonic() - t0) * 1000.0
                        raw_payload = dumps_scientific(payload)
                        rec = {
                            "protocol_id": PROTOCOL_VERSION,
                            "run_id": args.run_id,
                            "runtime_id": RUNTIME_DIGEST,
                            "system": system,
                            "condition": condition,
                            "replicate_index": rep,
                            "probe_index": probe,
                            "replicate_seed_sha256": digest.hex(),
                            "status": "EXECUTED",
                            "raw_metric_payload": payload,
                            "raw_payload_sha256": sha256_bytes(raw_payload.encode("utf-8")),
                            "timing": {"wall_ms": dt_ms},
                            "error_class": None,
                        }
                        line = dumps_scientific(rec) + "\n"
                        fh.write(line.encode("utf-8"))
                        n_a += 1
                    fh.flush()
                    if rep % 8 == 0:
                        print(f"TRACK_A {system}/{condition} rep={rep} rows={n_a}", flush=True)
        if n_a != 57344:
            raise StopError("STOP_STAGE_A_SEAL_FAILURE", f"track A rows {n_a}")
        print("TRACK_A complete 57344", flush=True)

        # --- Track B split ---
        ipc_rows = json.loads((receipts / "IPC_RESOLVED_ROWS.json").read_text())["rows"]
        split_seen: Dict[bytes, Tuple[str, str]] = {}
        keyed = []
        for item in ipc_rows:
            domain = item["domain_id"]
            rel = item["canonical_relative_path"]
            digest, pre = track_b_split(VERSION_DOI, domain, rel)
            if CONCEPT_DOI.encode("ascii") in pre:
                raise StopError("STOP_STAGE_A_SPLIT_COLLISION", "concept DOI in split preimage")
            key = (domain, rel)
            if digest in split_seen and split_seen[digest] != key:
                raise StopError("STOP_STAGE_A_SPLIT_COLLISION", digest.hex())
            split_seen[digest] = key
            keyed.append((digest, rel.encode("utf-8"), item))
        keyed.sort(key=lambda t: (t[0], t[1]))
        by_domain: Dict[str, int] = {}
        assigned = []
        for digest, _pb, item in keyed:
            domain = item["domain_id"]
            n = by_domain.get(domain, 0)
            if n < 8:
                split = "development"
            elif n < 20:
                split = "evaluation"
            else:
                split = "excluded_over_cap"
            by_domain[domain] = n + 1
            assigned.append((digest, split, item))
        n_dev = sum(1 for _, s, _ in assigned if s == "development")
        n_ev = sum(1 for _, s, _ in assigned if s == "evaluation")
        n_ex = sum(1 for _, s, _ in assigned if s == "excluded_over_cap")
        if not (n_dev == 32 and n_ev == 48 and n_ex == 40):
            raise StopError("STOP_STAGE_A_SPLIT_COLLISION", f"split counts {n_dev}/{n_ev}/{n_ex}")

        lilo = json.loads((receipts / "RUNTIME_PRECHECK.json").read_text())["lilotane"]
        binary = lilo["binary"]
        b_exec = 0
        track_b_lines = []
        raw_root = run_dir / "baseline_raw"
        for digest, split, item in assigned:
            uid = f"B|{item['domain_id']}|{item['canonical_relative_path']}"
            if uid in units:
                raise StopError("STOP_STAGE_A_DUPLICATE_UNIT", uid)
            units.add(uid)
            rec = {
                "domain": item["domain_id"],
                "canonical_path": item["canonical_relative_path"],
                "file_sha256": item["file_sha256"],
                "split_digest_sha256": digest.hex(),
                "assigned_split": split,
                "baseline_status": None,
                "wall_clock_s": None,
                "peak_rss_bytes": None,
                "exit_code": None,
                "timeout_applied": None,
                "oom_applied": None,
                "plan_nonempty": None,
                "raw_planner_output_sha256": None,
                "timing": None,
                "error_class": None,
                "protocol_id": PROTOCOL_VERSION,
                "run_id": args.run_id,
                "runtime_id": RUNTIME_DIGEST,
            }
            if split != "excluded_over_cap":
                work = raw_root / item["domain_id"] / item["canonical_relative_path"].replace("/", "_")
                try:
                    led = _run_lilotane(binary, item["domain_abs"], item["problem_abs"], work)
                except Exception as e:
                    raise StopError("STOP_STAGE_A_BASELINE_INFRASTRUCTURE_FAILURE", str(e)) from e
                rec.update({
                    "baseline_status": led["baseline_status"],
                    "wall_clock_s": led["wall_clock_s"],
                    "peak_rss_bytes": led["peak_rss_bytes"],
                    "exit_code": led["exit_code"],
                    "timeout_applied": led["timeout_applied"],
                    "oom_applied": led["oom_applied"],
                    "plan_nonempty": led["plan_nonempty"],
                    "raw_planner_output_sha256": led["raw_planner_output_sha256"],
                    "timing": {"wall_s": led["wall_clock_s"]},
                    "error_class": led["error_class"],
                })
                write_new_text(work / "ledger.json", dumps_scientific(led) + "\n")
                b_exec += 1
                print(f"BASELINE {item['domain_id']}/{item['canonical_relative_path']} {led['baseline_status']}", flush=True)
            track_b_lines.append(dumps_scientific(rec) + "\n")
        write_new_text(run_dir / "stage_a_track_b.jsonl", "".join(track_b_lines))
        if CONCEPT_DOI in (run_dir / "stage_a_track_b.jsonl").read_text(encoding="utf-8"):
            raise StopError("STOP_STAGE_A_SPLIT_COLLISION", "concept DOI leaked into track B")
        if b_exec != 80:
            raise StopError("STOP_STAGE_A_SEAL_FAILURE", f"baseline executed {b_exec}")

        n_b = sum(1 for _ in (run_dir / "stage_a_track_b.jsonl").open())
        if n_b != 120:
            raise StopError("STOP_STAGE_A_SEAL_FAILURE", f"track B rows {n_b}")

        if any(counters[k] != 0 for k in counters):
            raise StopError("STOP_STAGE_A_UNAUTHORIZED_LATER_STAGE", str(counters))

        root = _seal(run_dir)
        counts_doc = {
            "TRACK_A_PROBES": n_a,
            "TRACK_B_ROWS": n_b,
            "BASELINE_EXECUTIONS": b_exec,
            "IPC_DEVELOPMENT": n_dev,
            "IPC_EVALUATION": n_ev,
            "IPC_EXCLUDED_OVER_CAP": n_ex,
            "counters": counters,
            "STAGE_A_EVIDENCE_ROOT_SHA256": root,
        }
        write_new_text(run_dir / "STAGE_A_COUNTS.json", dumps_scientific(counts_doc) + "\n")
        verdict = "V0.5.6_STAGE_A_RAW_EXECUTION = PASS"
        write_new_text(run_dir / "FINAL_VERDICT.txt", verdict + "\n")
        write_new_text(receipts / "FINAL_VERDICT.txt", verdict + "\n")
        write_new_text(receipts / "STAGE_A_EVIDENCE_ROOT_SHA256.txt", root + "\n")
        print(f"SEAL root={root}")
        print(verdict)
    except StopError as e:
        _append_incident(run_dir, {"code": e.code, "detail": e.detail, "utc": utc_now()})
        try:
            if not (run_dir / "manifest.json").exists():
                # partial seal without overwrite
                _seal(run_dir)
        except Exception:
            pass
        record_stop(receipts, e.code, e.detail, consumed=True)
        raise


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", required=True)
    p.add_argument("--receipts-dir", required=True)
    p.add_argument("--protocol-dir", default="")
    p.add_argument("--run-dir", default="")
    p.add_argument("--auth-path", default="")
    p.add_argument("--run-id", default=RUN_ID_DEFAULT)
    p.add_argument("--wrapper-path", default="")
    p.add_argument("--zip-dir", default="")
    p.add_argument("--start-present", default="no")
    p.add_argument("--consumed", default="no")
    p.add_argument("--verdict", default="")
    args = p.parse_args()
    try:
        if args.phase == "host-public-protocol":
            phase_host_public_protocol(args)
        elif args.phase == "host-start":
            phase_host_start(args)
        elif args.phase == "host-package":
            phase_host_package(args)
        elif args.phase == "prestart":
            phase_prestart(args)
        elif args.phase == "science":
            phase_science(args)
        else:
            raise SystemExit(f"unknown phase {args.phase}")
        return 0
    except StopError as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:
        receipts = Path(args.receipts_dir)
        consumed = args.phase == "science" or (
            args.run_dir and Path(args.run_dir, "START_STAGE_A.json").exists()
        )
        record_stop(
            receipts,
            "STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE" if consumed else "STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE",
            f"{type(e).__name__}: {e}",
            consumed=bool(consumed),
        )
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
