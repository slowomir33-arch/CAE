#!/usr/bin/env python3
"""Regenerate Decoder6502.bin twice inside the immutable parent runtime.

NO Stage A. NO START_STAGE_A. NO RUN_AUTHORIZATION consumption.
Does not modify /opt/ott/sources. Does not trust a previously materialized binary.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
BREAK6502_COMMIT = "922af6496a2fa3b0a999e24419b5f8187f0ee98e"
LIBGATE_SHA256 = "ba8222d520c93ac8a3989857c8b2b3cb8573196ef185747eef60d8482dcf1964"
CANONICAL_BYTES = 272629760
CANONICAL_SHA256 = "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62"

LIB_CANDIDATES = [
    Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libgate6502.so"),
    Path("/workspace/systems/10_cpu_6502_libs/libgate6502.so"),
]
RECEIPTS = Path(os.environ.get("OTT_RECEIPTS_DIR", "/ott/receipts"))
OUT_DIR = Path(os.environ.get("OTT_OUT_DIR", "/ott/out"))

_GEN_CHILD = r"""
import ctypes, os, sys, time
scratch, libgate = sys.argv[1], sys.argv[2]
os.chdir(scratch)
t0 = time.monotonic()
lib = ctypes.CDLL(libgate)
lib.gate_init()
produced = os.path.isfile("Decoder6502.bin")
print("WALL=%.6f" % (time.monotonic() - t0))
print("PRODUCED=%s" % ("1" if produced else "0"))
"""


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_json(name: str, obj: Any) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / name).write_text(dumps(obj), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(path: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out if re.fullmatch(r"[0-9a-f]{40}", out) else None
    except Exception:
        return None


def stop(code: str, detail: Dict[str, Any]) -> int:
    write_json("FREEZE_STOP.json", {"stop": code, **detail})
    (RECEIPTS / "FREEZE_STOP.txt").write_text(code + "\n", encoding="utf-8")
    print(code, flush=True)
    return 2


def generate(libgate: Path, scratch: Path) -> Dict[str, Any]:
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    proc = subprocess.run(
        [sys.executable, "-c", _GEN_CHILD, str(scratch), str(libgate.resolve())],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        timeout=3600,
        env={"PYTHONUNBUFFERED": "1", "PATH": os.environ.get("PATH", ""), "HOME": str(scratch)},
    )
    produced = scratch / "Decoder6502.bin"
    rec: Dict[str, Any] = {
        "command": "fresh-process: chdir(scratch); ctypes.CDLL(libgate6502.so).gate_init()  # M6502(true,false) HLE",
        "scratch": str(scratch),
        "exit_code": proc.returncode,
        "produced": produced.is_file(),
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }
    if produced.is_file():
        rec["byte_size"] = produced.stat().st_size
        rec["sha256"] = sha256_file(produced)
    return rec


def main() -> int:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    digest_env = os.environ.get("OTT_RUNTIME_DIGEST", RUNTIME_DIGEST)
    cae = Path("/opt/ott/sources/CAE")
    brk = Path("/opt/ott/sources/break6502")
    cae_head = git_head(cae)
    brk_head = git_head(brk)
    lib = next((p for p in LIB_CANDIDATES if p.is_file()), None)
    ident = {
        "pulled_digest_env": digest_env,
        "cae_head": cae_head,
        "break6502_head": brk_head,
        "libgate": str(lib) if lib else None,
        "libgate_sha256": sha256_file(lib) if lib else None,
    }
    write_json("PARENT_RUNTIME_IDENTITY.json", ident)
    if digest_env != RUNTIME_DIGEST:
        return stop("STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE", ident)
    if cae_head != CAE_COMMIT or brk_head != BREAK6502_COMMIT or lib is None:
        return stop("STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE", ident)
    if ident["libgate_sha256"] != LIBGATE_SHA256:
        return stop("STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE", ident)

    g1 = generate(lib, Path("/tmp/ott-d6502f-gen1"))
    g2 = generate(lib, Path("/tmp/ott-d6502f-gen2"))
    gen_doc = {"gen1": g1, "gen2": g2}
    write_json("GENERATION_IDENTITY.json", gen_doc)
    ok = (
        g1.get("produced")
        and g2.get("produced")
        and g1.get("byte_size") == CANONICAL_BYTES
        and g2.get("byte_size") == CANONICAL_BYTES
        and g1.get("sha256") == CANONICAL_SHA256
        and g2.get("sha256") == CANONICAL_SHA256
        and g1.get("sha256") == g2.get("sha256")
    )
    if not ok:
        return stop("STOP_D6502_SUPPLEMENT_REGENERATION_MISMATCH", gen_doc)

    src = Path("/tmp/ott-d6502f-gen1/Decoder6502.bin")
    dst = OUT_DIR / "Decoder6502.bin"
    shutil.copy2(src, dst)
    if sha256_file(dst) != CANONICAL_SHA256 or dst.stat().st_size != CANONICAL_BYTES:
        return stop("STOP_D6502_SUPPLEMENT_REGENERATION_MISMATCH", {"copy": sha256_file(dst)})
    gen_doc["canonical_payload"] = str(dst)
    gen_doc["REGENERATION"] = "PASS"
    write_json("GENERATION_IDENTITY.json", gen_doc)
    for p in (src, Path("/tmp/ott-d6502f-gen2/Decoder6502.bin")):
        try:
            p.unlink()
        except Exception:
            pass
    print("REGENERATION_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
