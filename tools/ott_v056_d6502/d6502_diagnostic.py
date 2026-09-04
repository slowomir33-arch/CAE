#!/usr/bin/env python3
"""OTT v0.5.6 Decoder6502 PRESTART diagnostic. Runs inside the immutable image.

NO Stage A. NO START_STAGE_A. NO RUN_AUTHORIZATION consumption.
NO VERSION_DOI seeds. NO IPC split. Does not modify /opt/ott/sources.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
BREAK6502_COMMIT = "922af6496a2fa3b0a999e24419b5f8187f0ee98e"
NUMPY_VERSION = "2.2.0"
PARENT_STAGE_A_RUN_ID = "OTT-v0.5.6-SCA-20260904T105201Z-BC6F6E8E"
GITHUB_PARENT_RUN_ID = "33865237389"
AUTH_SHA = "4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358"
PROTOCOL_ROOT = "b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516"

EXPLICIT = [
    Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/Decoder6502.bin"),
    Path("/opt/ott/sources/break6502/test/Decoder6502.bin"),
]
EXTRA_EXPLICIT = [
    Path("/workspace/systems/10_cpu_6502_libs/Decoder6502.bin"),
]
LIB_CANDIDATES = [
    Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libgate6502.so"),
    Path("/workspace/systems/10_cpu_6502_libs/libgate6502.so"),
]
SCRATCH_ROOT = Path("/tmp/ott-d6502-smoke")
RECEIPTS = Path(os.environ.get("OTT_RECEIPTS_DIR", "/ott/receipts"))

# Fresh-process HLE construction. gate_init() is in-process idempotent, so D4
# must not share a process between GEN1 and GEN2.
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


def find_git_head(expected: str, roots: List[Path]) -> tuple[Optional[Path], Optional[str]]:
    last: Optional[str] = None
    for root in roots:
        if not root.exists():
            continue
        h = git_head(root)
        if h:
            last = h
        if h == expected:
            return root, h
        try:
            n = 0
            for p in root.rglob(".git"):
                cand = p.parent
                h = git_head(cand)
                if h:
                    last = h
                if h == expected:
                    return cand, h
                n += 1
                if n > 40:
                    break
        except Exception:
            pass
    return None, last


def file_record(path: Path) -> Dict[str, Any]:
    st = path.stat()
    return {
        "absolute_path": str(path.resolve()),
        "byte_size": st.st_size,
        "sha256": sha256_file(path),
        "mode": oct(st.st_mode),
        "mtime_unix": int(st.st_mtime),
        "inode": st.st_ino,
        "device": st.st_dev,
    }


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def classify_and_report(classification: str, extra: Dict[str, Any]) -> None:
    diag_id = os.environ.get("OTT_DIAGNOSTIC_ID", "")
    doc = {
        "document": "D6502_CLASSIFICATION",
        "diagnostic_id": diag_id,
        "D6502_CLASSIFICATION": classification,
        "RUN_AUTHORIZATION_CONSUMED": "NO",
        "START_STAGE_A": "ABSENT",
        "SCIENTIFIC_OBSERVATIONS": 0,
        "STAGE_A_EXECUTION": "NO",
        "parent_stage_a_run_id": PARENT_STAGE_A_RUN_ID,
        "github_parent_run_id": GITHUB_PARENT_RUN_ID,
        **extra,
    }
    write_json("D6502_CLASSIFICATION.json", doc)
    (RECEIPTS / "D6502_CLASSIFICATION.txt").write_text(classification + "\n", encoding="utf-8")
    report = f"""# OTT v0.5.6 — DECODER6502 PRESTART DIAGNOSTIC REPORT

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: DECODER6502_PRESTART_DIAGNOSTIC
RUN_ID: {diag_id}
MESSAGE_ID: {diag_id}-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: {utc_now()}
AGENT: Cursor/GitHub Actions Decoder6502 diagnostic
PARENT_STAGE_A_RUN_ID: {PARENT_STAGE_A_RUN_ID}
GITHUB_PARENT_RUN_ID: {GITHUB_PARENT_RUN_ID}
PUBLIC_PROTOCOL_ROOT_SHA256: {PROTOCOL_ROOT}
RUN_AUTHORIZATION_SHA256: {AUTH_SHA}
RUNTIME_DIGEST: {RUNTIME_DIGEST}
END_OTT_REPORT_SIGNATURE

```
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
STAGE_A_EXECUTION = NO

D6502_CLASSIFICATION = {classification}
```

{json.dumps(extra, indent=2, sort_keys=True)}
"""
    (RECEIPTS / "D6502_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (RECEIPTS / "DIAGNOSTIC_ID.txt").write_text(diag_id + "\n", encoding="utf-8")
    print(f"D6502_CLASSIFICATION = {classification}", flush=True)


def phase_d1() -> Dict[str, Any]:
    import numpy as np

    uname = os.uname()
    digest_env = os.environ.get("OTT_RUNTIME_DIGEST", RUNTIME_DIGEST)
    ws = Path("/workspace")
    cae_alt = Path("/opt/ott/sources/CAE")
    if (ws / "systems" / "10_cpu_6502.py").is_file():
        cae = ws
    elif (cae_alt / "systems" / "10_cpu_6502.py").is_file():
        cae = cae_alt
    else:
        raise RuntimeError("pinned CAE tree not found")
    cae_path, cae_head = find_git_head(CAE_COMMIT, [cae, cae_alt, Path("/opt/ott/sources")])
    brk = Path("/opt/ott/sources/break6502")
    if not brk.exists():
        for cand in Path("/opt/ott/sources").glob("*break6502*"):
            if cand.is_dir():
                brk = cand
                break
    brk_path, brk_head = find_git_head(BREAK6502_COMMIT, [brk, Path("/opt/ott/sources")])
    lib = next((p for p in LIB_CANDIDATES if p.is_file()), None)
    if digest_env != RUNTIME_DIGEST:
        raise RuntimeError(f"digest env {digest_env}")
    if cae_head != CAE_COMMIT:
        raise RuntimeError(f"CAE HEAD {cae_head}")
    if brk_head != BREAK6502_COMMIT:
        raise RuntimeError(f"break6502 HEAD {brk_head}")
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"numpy {np.__version__}")
    if lib is None:
        raise RuntimeError("libgate6502.so missing")
    ident = {
        "pulled_digest_required": RUNTIME_DIGEST,
        "pulled_digest_env": digest_env,
        "platform": {"sysname": uname.sysname, "machine": uname.machine},
        "cae_path": str(cae),
        "cae_git_path": str(cae_path) if cae_path else None,
        "cae_head": cae_head,
        "break6502_path": str(brk_path or brk),
        "break6502_head": brk_head,
        "numpy": np.__version__,
        "libgate6502.so": file_record(lib),
        "PASS": True,
    }
    write_json("RUNTIME_IDENTITY.json", ident)
    return {"cae": cae, "break6502": brk_path or brk, "libgate": lib, "ident": ident}


def phase_d2() -> List[Dict[str, Any]]:
    found: List[Path] = []
    src = Path("/opt/ott/sources")
    find_stdout = ""
    find_rc = None
    if src.exists():
        proc = subprocess.run(
            ["find", str(src), "-type", "f", "-name", "Decoder6502.bin", "-print"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        find_rc = proc.returncode
        find_stdout = proc.stdout or ""
        for line in find_stdout.splitlines():
            p = Path(line.strip())
            if p.is_file():
                found.append(p)
    explicit_status = {}
    for p in EXPLICIT + EXTRA_EXPLICIT:
        explicit_status[str(p)] = p.is_file()
        if p.is_file() and p.resolve() not in {x.resolve() for x in found}:
            found.append(p)
    uniq: List[Path] = []
    seen = set()
    for p in found:
        r = str(p.resolve())
        if r not in seen:
            seen.add(r)
            uniq.append(p.resolve())
    records = [file_record(p) for p in uniq]
    write_json(
        "DECODER6502_DISCOVERY.json",
        {
            "find_command": "find /opt/ott/sources -type f -name Decoder6502.bin -print",
            "find_returncode": find_rc,
            "find_stdout": find_stdout,
            "explicit_exists": explicit_status,
            "n_copies": len(records),
            "copies": records,
        },
    )
    return records


def _hle_ctor_evidence(cae: Path) -> Dict[str, Any]:
    candidates = [
        cae / "systems" / "10_cpu_6502_libs" / "gate_bridge.cpp",
        Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/gate_bridge.cpp"),
        Path("/workspace/systems/10_cpu_6502_libs/gate_bridge.cpp"),
    ]
    needle = "M6502Core::M6502(true, false)"
    needle_alt = "M6502Core::M6502(true,false)"
    hits = []
    for p in candidates:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if needle in text or needle_alt in text:
            hits.append({"path": str(p.resolve()), "ctor": needle})
    return {"gate_bridge_hits": hits, "unique": bool(hits)}


def analyze_generator(break_root: Path, cae: Path) -> Dict[str, Any]:
    hits: List[Dict[str, Any]] = []
    if break_root.exists():
        for p in break_root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".cpp", ".c", ".h", ".hpp", ".cc", ".md", ".txt"}:
                continue
            if p.stat().st_size > 2_000_000:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if "Decoder6502.bin" in text:
                lines = []
                for i, ln in enumerate(text.splitlines(), 1):
                    if "Decoder6502.bin" in ln or "HLE" in ln:
                        lines.append({"line": i, "text": ln.strip()[:240]})
                hits.append(
                    {
                        "path": str(p),
                        "rel": str(p.relative_to(break_root)) if str(p).startswith(str(break_root)) else str(p),
                        "mentions": lines[:40],
                    }
                )
    hle = _hle_ctor_evidence(cae)
    unique = bool(hle.get("unique"))
    analysis = {
        "break6502_root": str(break_root),
        "source_hits": hits,
        "hle_ctor": hle,
        "cae_facts": {
            "cae_gate_init": "systems/10_cpu_6502_libs/gate_bridge.cpp :: gate_init → new M6502Core::M6502(true, false)  # HLE=true",
            "python_requires_existing_file": True,
            "python_will_not_generate": "GateSimulator raises FileNotFoundError before gate_init if Decoder6502.bin is absent next to the .so",
            "direct_gate_init_in_scratch_cwd": "calling unmodified libgate6502.so gate_init() after chdir(scratch) in a fresh process is the unique frozen HLE construction path",
        },
        "expected_working_directory": "CWD at M6502 construction / gate_init (Decoder6502.bin is read/written relative to CWD)",
        "expected_output_path": "<cwd>/Decoder6502.bin",
        "required_command": [
            "fresh python process",
            "chdir(scratch)",
            "ctypes.CDLL(libgate6502.so).gate_init()",
        ],
        "uses_version_doi": False,
        "uses_scientific_seed": False,
        "network": False,
        "clock_host_data_in_command": "not present in the frozen invocation; any hidden host entropy would surface as D4 hash mismatch",
        "mechanically_unique_generator": unique,
        "ambiguity": None if unique else "STOP_D6502_GENERATOR_AMBIGUOUS: HLE M6502(true, false) ctor not found in pinned gate_bridge.cpp",
    }
    md = [
        "# BREAK6502 generator analysis (diagnostic only)",
        "",
        "Pinned CAE `gate_init()` constructs `M6502Core::M6502(true, false)` (HLE=true).",
        "THIRD_PARTY: first HLE construction generates `Decoder6502.bin` in the working directory.",
        "Python `GateSimulator` refuses to call `gate_init` if the file is missing; the diagnostic",
        "therefore uses the unmodified shared library `gate_init()` in a scratch CWD for D4.",
        "Each D4 generation runs in a **fresh process** because `gate_init()` is in-process idempotent.",
        "",
        "No VERSION_DOI. No scientific seed. No modification of `/opt/ott/sources`.",
        "",
        dumps(analysis),
    ]
    (RECEIPTS / "BREAK6502_GENERATOR_ANALYSIS.md").write_text("\n".join(md), encoding="utf-8")
    return analysis


def _load_cpu_module(cae: Path):
    path = cae / "systems" / "10_cpu_6502.py"
    if not path.is_file():
        path = Path("/workspace/systems/10_cpu_6502.py")
    if not path.is_file():
        path = Path("/opt/ott/sources/CAE/systems/10_cpu_6502.py")
    if str(path.parent.parent) not in sys.path:
        sys.path.insert(0, str(path.parent.parent))
    spec = importlib.util.spec_from_file_location("cpu_6502_d6502_diag", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def smoke_gatesimulator(lib_dir: Path, cae: Path) -> Dict[str, Any]:
    os.environ["CPU6502_LIB_DIR"] = str(lib_dir)
    cpu = _load_cpu_module(cae)
    t0 = time.monotonic()
    sim = cpu.GateSimulator()
    # Sentinel NOP 0xEA, ilen=1, all register inputs 0. Not DOI-derived.
    ao, xo, yo, so, po = sim._exec(0xEA, 0, 1, 0, 0, 0, 0, 0)
    rec = {
        "CPU6502_LIB_DIR": str(lib_dir),
        "gate_init": "PASS",
        "sentinel": {
            "opcode": 0xEA,
            "operand": 0,
            "ilen": 1,
            "A_in": 0,
            "X_in": 0,
            "Y_in": 0,
            "S_in": 0,
            "P_in": 0,
        },
        "outputs": {"A_out": ao, "X_out": xo, "Y_out": yo, "S_out": so, "P_out": po},
        "wall_s": time.monotonic() - t0,
        "scientific": False,
        "PASS": True,
    }
    write_json("GATESIMULATOR_SMOKE.json", rec)
    return rec


def stage_scratch_lib(libgate: Path, decoder: Path, dest: Path, method: str) -> Dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    so_dst = dest / "libgate6502.so"
    bin_dst = dest / "Decoder6502.bin"
    if method == "symlink":
        if so_dst.exists() or so_dst.is_symlink():
            so_dst.unlink()
        if bin_dst.exists() or bin_dst.is_symlink():
            bin_dst.unlink()
        os.symlink(str(libgate.resolve()), str(so_dst))
        os.symlink(str(decoder.resolve()), str(bin_dst))
    else:
        shutil.copy2(libgate, so_dst)
        shutil.copy2(decoder, bin_dst)
    return {
        "method": method,
        "lib_dir": str(dest),
        "libgate6502.so": str(so_dst),
        "Decoder6502.bin": str(bin_dst),
        "modified_opt_ott_sources": False,
    }


def generate_via_gate_init(libgate: Path, scratch: Path) -> Dict[str, Any]:
    scratch.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
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
        "wall_s": time.monotonic() - t0,
        "produced": produced.is_file(),
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }
    if produced.is_file():
        rec["byte_size"] = produced.stat().st_size
        rec["sha256"] = sha256_file(produced)
    return rec


def _copies_in_immutable_image(copies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    inside = []
    for c in copies:
        p = str(c.get("absolute_path", ""))
        if p.startswith("/opt/ott/"):
            inside.append(c)
    return inside


def main() -> int:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    try:
        d1 = phase_d1()
        copies = phase_d2()
        analysis = analyze_generator(Path(d1["break6502"]), Path(d1["cae"]))
        image_copies = _copies_in_immutable_image(copies)
        hashes = {c["sha256"] for c in image_copies}
        if image_copies:
            if len(hashes) > 1:
                classify_and_report(
                    "C_RUNTIME_SUPERSESSION_REQUIRED",
                    {"stop": "STOP_D6502_MULTIPLE_NONIDENTICAL_COPIES", "copies": image_copies},
                )
                return 2
            decoder = Path(image_copies[0]["absolute_path"])
            staged = stage_scratch_lib(Path(d1["libgate"]), decoder, SCRATCH_ROOT / "lib", "symlink")
            try:
                smoke = smoke_gatesimulator(SCRATCH_ROOT / "lib", Path(d1["cae"]))
            except Exception as e:
                traceback.print_exc()
                classify_and_report(
                    "C_RUNTIME_SUPERSESSION_REQUIRED",
                    {
                        "stop": "STOP_D6502_SMOKE_FAILURE",
                        "error": f"{type(e).__name__}: {e}",
                        "scratch": staged,
                        "decoder": image_copies[0],
                    },
                )
                return 2
            classify_and_report(
                "A_EXISTING_IMMUTABLE_BYTE_RELOCATION",
                {
                    "SCIENTIFIC_SEMANTICS_DELTA": 0,
                    "NEW_EXTERNAL_RUNTIME_BYTES": 0,
                    "D6502_EXISTING_IMAGE_BYTE_RELOCATION": "PASS",
                    "decoder": image_copies[0],
                    "scratch": staged,
                    "smoke": smoke,
                },
            )
            return 0
        # D3B / D4 / D5 — no Decoder6502.bin under /opt/ott/sources
        if not analysis.get("mechanically_unique_generator"):
            classify_and_report(
                "C_RUNTIME_SUPERSESSION_REQUIRED",
                {"stop": "STOP_D6502_GENERATOR_AMBIGUOUS", "analysis": analysis},
            )
            return 2
        gen1_dir = Path("/tmp/ott-d6502-gen1")
        gen2_dir = Path("/tmp/ott-d6502-gen2")
        g1 = generate_via_gate_init(Path(d1["libgate"]), gen1_dir)
        g2 = generate_via_gate_init(Path(d1["libgate"]), gen2_dir)
        det = {"gen1": g1, "gen2": g2}
        write_json("DECODER6502_DETERMINISM.json", det)
        if not g1.get("produced") or not g2.get("produced"):
            classify_and_report(
                "C_RUNTIME_SUPERSESSION_REQUIRED",
                {"stop": "STOP_D6502_GENERATOR_AMBIGUOUS", "determinism": det, "g1": g1, "g2": g2},
            )
            return 2
        if g1["sha256"] != g2["sha256"] or g1["byte_size"] != g2["byte_size"]:
            classify_and_report(
                "C_RUNTIME_SUPERSESSION_REQUIRED",
                {"stop": "STOP_D6502_GENERATION_NONDETERMINISTIC", "determinism": det},
            )
            return 2
        write_json(
            "DECODER6502_DETERMINISM.json",
            {**det, "D6502_DETERMINISTIC_GENERATION": "PASS"},
        )
        smoke_dir = SCRATCH_ROOT / "generated-lib"
        staged = stage_scratch_lib(Path(d1["libgate"]), gen1_dir / "Decoder6502.bin", smoke_dir, "copy")
        try:
            smoke = smoke_gatesimulator(smoke_dir, Path(d1["cae"]))
        except Exception as e:
            traceback.print_exc()
            classify_and_report(
                "C_RUNTIME_SUPERSESSION_REQUIRED",
                {
                    "stop": "STOP_D6502_SMOKE_FAILURE",
                    "error": f"{type(e).__name__}: {e}",
                    "determinism": det,
                    "scratch": staged,
                },
            )
            return 2
        for p in (gen1_dir / "Decoder6502.bin", gen2_dir / "Decoder6502.bin", smoke_dir / "Decoder6502.bin"):
            try:
                if p.is_file() and not p.is_symlink():
                    p.unlink()
            except Exception:
                pass
        classify_and_report(
            "B_DETERMINISTIC_RUNTIME_SUPPLEMENT_REQUIRED",
            {
                "D6502_DETERMINISTIC_GENERATION": "PASS",
                "D6502_GENERATED_SCRATCH_SMOKE": "PASS",
                "DECODER6502_SHA256": g1["sha256"],
                "DECODER6502_BYTES": g1["byte_size"],
                "GENERATOR_COMMAND": g1["command"],
                "GENERATOR_SOURCE_IDENTITY": {
                    "cae_commit": CAE_COMMIT,
                    "break6502_commit": BREAK6502_COMMIT,
                    "libgate6502_sha256": d1["ident"]["libgate6502.so"]["sha256"],
                    "hle": "M6502(true, false)",
                },
                "scratch": staged,
                "smoke": smoke,
            },
        )
        return 0
    except Exception as e:
        traceback.print_exc()
        classify_and_report(
            "C_RUNTIME_SUPERSESSION_REQUIRED",
            {"stop": "STOP_D6502_RUNTIME_IDENTITY_FAILURE", "error": f"{type(e).__name__}: {e}"},
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
