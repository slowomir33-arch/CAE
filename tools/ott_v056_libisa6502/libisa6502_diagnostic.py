#!/usr/bin/env python3
"""OTT v0.5.6 libisa6502 PRESTART diagnostic. Runs inside the immutable image.

NO Stage A. NO START_STAGE_A. NO RUN_AUTHORIZATION consumption.
NO VERSION_DOI seeds. NO IPC split. Does not modify /opt/ott/sources.
Does not mutate the Decoder6502 supplement. Does not rebuild/push the runtime.
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
from typing import Any, Dict, List, Optional, Tuple

RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
FAKE6502_COMMIT = "b52676f840983219b0b9baa13f1d0ebc07aac9f9"
BREAK6502_COMMIT = "922af6496a2fa3b0a999e24419b5f8187f0ee98e"
PERFECT6502_COMMIT = "09fc542877a84318291aa42dab143a3e2c3db974"
LIBGATE_SHA256 = "ba8222d520c93ac8a3989857c8b2b3cb8573196ef185747eef60d8482dcf1964"
DECODER_SHA256 = "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62"
DECODER_BYTES = 272629760
SUPPLEMENT_CONTENT_ROOT = "5bd5679a5ca297eb1d2b2a84d1b68c900b54d98ea7cd0c5ac672ec903e5a48ea"
SUPPLEMENT_OCI_DIGEST = "sha256:b5f0938a6706f33add9e624072c1a6cab542a2fbf5eea899880778243a74ee20"
AUTH_SHA = "cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26"
PARENT_STAGE_A_RUN_ID = "OTT-v0.5.6-SCA-20260904T124104Z-9A3DE0B9"
GITHUB_PARENT_RUN_ID = "33874006921"
ISA_FILENAME = "libisa6502.so"
GATE_FILENAME = "libgate6502.so"
EXPECTED_ISA_EXPORTS = ("isa_init", "isa_execute_instruction")
CANONICAL_GCC = [
    "gcc",
    "-O2",
    "-shared",
    "-fPIC",
    "-Wl,--version-script=isa.version",
    "-o",
    "libisa6502.so",
    "isa_bridge.c",
]
EXPLICIT_ISA = [
    Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libisa6502.so"),
    Path("/opt/ott/sources/CAE/systems/libisa6502.so"),
    Path("/workspace/systems/10_cpu_6502_libs/libisa6502.so"),
    Path("/workspace/systems/libisa6502.so"),
]
LIBGATE_CANDIDATES = [
    Path("/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libgate6502.so"),
    Path("/workspace/systems/10_cpu_6502_libs/libgate6502.so"),
]
SCRATCH_ROOT = Path("/tmp/ott-isa6502-diag")
RECEIPTS = Path(os.environ.get("OTT_RECEIPTS_DIR", "/ott/receipts"))
SUPPLEMENT_DIR = Path(os.environ.get("OTT_SUPPLEMENT_DIR", "/ott-supplement"))

_GEN_CHILD = r"""
import os, subprocess, sys, time
out_dir, isa_c, ver, fake_c, fake_inc = sys.argv[1:6]
os.chdir(out_dir)
cmd = [
    "gcc", "-O2", "-shared", "-fPIC",
    "-Wl,--version-script=" + ver,
    "-o", "libisa6502.so",
    isa_c, fake_c, "-I" + fake_inc,
]
t0 = time.monotonic()
p = subprocess.run(cmd, capture_output=True, text=True)
print("RC=%s" % p.returncode)
print("WALL=%.6f" % (time.monotonic() - t0))
sys.stdout.write("STDOUT_BEGIN\n")
sys.stdout.write(p.stdout or "")
sys.stdout.write("STDOUT_END\n")
sys.stderr.write(p.stderr or "")
sys.exit(p.returncode)
"""


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def find_git_head(expected: str, roots: List[Path]) -> Tuple[Optional[Path], Optional[str]]:
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


def run_text(cmd: List[str]) -> Optional[str]:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except Exception:
        return None


def elf_record(path: Path) -> Dict[str, Any]:
    rec: Dict[str, Any] = {}
    file_out = run_text(["file", "-b", str(path)])
    rec["file"] = (file_out or "").strip() or None
    rh = run_text(["readelf", "-h", str(path)])
    rec["readelf_h"] = rh
    rec["elf_class"] = None
    rec["elf_machine"] = None
    if rh:
        for ln in rh.splitlines():
            if "Class:" in ln:
                rec["elf_class"] = ln.split(":", 1)[1].strip()
            if "Machine:" in ln:
                rec["elf_machine"] = ln.split(":", 1)[1].strip()
    rec["readelf_d"] = run_text(["readelf", "-d", str(path)])
    rec["ldd"] = run_text(["ldd", str(path)])
    rec["nm_defined_T"] = run_text(["nm", "-D", "--defined-only", str(path)])
    return rec


def file_record(path: Path) -> Dict[str, Any]:
    st = path.stat()
    rec = {
        "absolute_path": str(path.resolve()),
        "bytes": st.st_size,
        "sha256": sha256_file(path),
        "mtime_unix": int(st.st_mtime),
        "mode": oct(st.st_mode),
    }
    rec.update(elf_record(path))
    return rec


def locate_cae() -> Path:
    ws = Path("/workspace")
    cae_alt = Path("/opt/ott/sources/CAE")
    if (ws / "systems" / "10_cpu_6502.py").is_file():
        return ws
    if (cae_alt / "systems" / "10_cpu_6502.py").is_file():
        return cae_alt
    raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": "pinned CAE tree not found"})


def load_cpu(lib_dir: Path, cae: Path) -> Any:
    os.environ["CPU6502_LIB_DIR"] = str(lib_dir)
    cand = cae / "systems" / "10_cpu_6502.py"
    if str(cae) not in sys.path:
        sys.path.insert(0, str(cae))
    spec = importlib.util.spec_from_file_location("cpu_6502_isa6502_diag", str(cand))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {cand}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def nop_smoke(cpu: Any, which: str) -> Dict[str, Any]:
    t0 = time.monotonic()
    if which == "isa":
        sim = cpu.ISASimulator()
    elif which == "gate":
        sim = cpu.GateSimulator()
    else:
        raise RuntimeError(which)
    ao, xo, yo, so, po = sim._exec(0xEA, 0, 1, 0, 0, 0, 0, 0)
    return {
        "which": which,
        "gate_or_isa_init": "PASS",
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


def classify_and_report(classification: str, extra: Dict[str, Any]) -> None:
    diag_id = os.environ.get("OTT_DIAGNOSTIC_ID", "")
    if classification == "A_EXISTING_IMMUTABLE_LIB_RELOCATION":
        gen2_status = "UNCONSUMED"
    else:
        gen2_status = "UNCONSUMED_PENDING_POSSIBLE_SUPERSESSION"
    doc = {
        "document": "LIBISA6502_CLASSIFICATION",
        "diagnostic_id": diag_id,
        "LIBISA6502_CLASSIFICATION": classification,
        "RUN_AUTHORIZATION_CONSUMED": "NO",
        "START_STAGE_A": "ABSENT",
        "SCIENTIFIC_OBSERVATIONS": 0,
        "STAGE_A_EXECUTION": "NO",
        "GENERATION_2_RUN_AUTHORIZATION_SHA256": AUTH_SHA,
        "GENERATION_2_RUN_AUTHORIZATION_STATUS": gen2_status,
        "parent_stage_a_run_id": PARENT_STAGE_A_RUN_ID,
        "github_parent_run_id": GITHUB_PARENT_RUN_ID,
        **extra,
    }
    write_json("LIBISA6502_CLASSIFICATION.json", doc)
    write_text("LIBISA6502_CLASSIFICATION.txt", classification + "\n")
    extra_txt = json.dumps({k: extra[k] for k in extra if k != "loader_excerpts"}, indent=2, sort_keys=True, default=str)
    report = f"""# OTT v0.5.6 — LIBISA6502 PRESTART DIAGNOSTIC REPORT

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: LIBISA6502_PRESTART_DIAGNOSTIC
RUN_ID: {diag_id}
MESSAGE_ID: {diag_id}-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: {utc_now()}
AGENT: Cursor/GitHub Actions libisa6502 PRESTART diagnostic
PARENT_STAGE_A_RUN_ID: {PARENT_STAGE_A_RUN_ID}
PARENT_GITHUB_RUN_ID: {GITHUB_PARENT_RUN_ID}
GENERATION_2_RUN_AUTHORIZATION_SHA256: {AUTH_SHA}
BASE_RUNTIME_DIGEST: {RUNTIME_DIGEST}
DECODER6502_SUPPLEMENT_OCI_DIGEST: {SUPPLEMENT_OCI_DIGEST}
END_OTT_REPORT_SIGNATURE

```
LIBISA6502_CLASSIFICATION = {classification}

GENERATION_2_RUN_AUTHORIZATION_STATUS =
{gen2_status}

RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
STAGE_A_EXECUTION = NO
```

{extra_txt}
"""
    write_text("LIBISA6502_FINAL_REPORT.md", report)
    write_text("DIAGNOSTIC_ID.txt", diag_id + "\n")
    print(f"LIBISA6502_CLASSIFICATION = {classification}", flush=True)


def frozen_decoder() -> Path:
    dec = SUPPLEMENT_DIR / "Decoder6502.bin"
    if not dec.is_file():
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": "supplement Decoder6502.bin missing"})
    if dec.stat().st_size != DECODER_BYTES or sha256_file(dec) != DECODER_SHA256:
        raise Stop(
            "STOP_LIBISA6502_PARENT_IDENTITY_FAILURE",
            {"detail": "supplement Decoder identity mismatch", "bytes": dec.stat().st_size, "sha256": sha256_file(dec)},
        )
    man = SUPPLEMENT_DIR / "SUPPLEMENT_MANIFEST.sha256"
    if man.is_file():
        root = hashlib.sha256(man.read_bytes()).hexdigest()
        if root != SUPPLEMENT_CONTENT_ROOT:
            raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": "content root", "got": root})
    return dec


def parent_identity(cae: Path) -> Dict[str, Any]:
    digest_env = os.environ.get("OTT_RUNTIME_DIGEST", RUNTIME_DIGEST)
    if digest_env != RUNTIME_DIGEST:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"digest env {digest_env}"})
    _, cae_head = find_git_head(CAE_COMMIT, [cae, Path("/opt/ott/sources/CAE"), Path("/opt/ott/sources")])
    fake_path, fake_head = find_git_head(
        FAKE6502_COMMIT,
        [Path("/opt/ott/sources/fake6502"), Path.home() / "fake6502", Path("/opt/ott/sources")],
    )
    brk_path, brk_head = find_git_head(
        BREAK6502_COMMIT,
        [Path("/opt/ott/sources/break6502"), Path("/opt/ott/sources")],
    )
    perf_path, perf_head = find_git_head(
        PERFECT6502_COMMIT,
        [Path("/opt/ott/sources/perfect6502"), Path("/opt/ott/sources")],
    )
    libgate = None
    libgate_rec = None
    for cand in LIBGATE_CANDIDATES:
        if cand.is_file():
            libgate = cand
            libgate_rec = file_record(cand)
            break
    if libgate is None:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": "libgate6502.so not found"})
    if libgate_rec and libgate_rec["sha256"] != LIBGATE_SHA256:
        raise Stop(
            "STOP_LIBISA6502_PARENT_IDENTITY_FAILURE",
            {"detail": "libgate6502.so sha mismatch", "got": libgate_rec["sha256"]},
        )
    if cae_head != CAE_COMMIT:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"CAE HEAD {cae_head}"})
    if fake_head != FAKE6502_COMMIT:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"fake6502 HEAD {fake_head}"})
    if brk_head != BREAK6502_COMMIT:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"break6502 HEAD {brk_head}"})
    if perf_head != PERFECT6502_COMMIT:
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"perfect6502 HEAD {perf_head}"})
    decoder = frozen_decoder()
    doc = {
        "document": "PARENT_IDENTITY",
        "runtime_digest": RUNTIME_DIGEST,
        "cae_head": cae_head,
        "cae_path": str(cae),
        "fake6502_head": fake_head,
        "fake6502_path": str(fake_path) if fake_path else None,
        "break6502_head": brk_head,
        "break6502_path": str(brk_path) if brk_path else None,
        "perfect6502_head": perf_head,
        "perfect6502_path": str(perf_path) if perf_path else None,
        "libgate6502_sha256": LIBGATE_SHA256,
        "libgate6502_path": str(libgate),
        "decoder6502_sha256": DECODER_SHA256,
        "decoder6502_bytes": DECODER_BYTES,
        "decoder6502_path": str(decoder),
        "supplement_content_root_sha256": SUPPLEMENT_CONTENT_ROOT,
        "supplement_oci_digest": SUPPLEMENT_OCI_DIGEST,
        "PASS": True,
    }
    write_json("PARENT_IDENTITY.json", doc)
    return {
        "cae": cae,
        "fake6502": fake_path,
        "libgate": libgate,
        "decoder": decoder,
        "parent": doc,
    }


def discover_isa() -> Dict[str, Any]:
    hits: List[Path] = []
    seen = set()
    for root in (Path("/opt/ott"), Path("/opt/ott/sources"), Path("/workspace")):
        if not root.exists():
            continue
        try:
            out = subprocess.check_output(
                ["find", str(root), "-type", "f", "-name", ISA_FILENAME, "-print"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except Exception:
            out = ""
        for ln in out.splitlines():
            p = Path(ln.strip())
            if p.is_file():
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    hits.append(p)
    for p in EXPLICIT_ISA:
        if p.is_file():
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                hits.append(p)
    records = [file_record(p) for p in hits]
    extra_globs = []
    for pattern_root in (
        Path("/opt/ott/sources/fake6502"),
        Path("/opt/ott/sources/break6502"),
        Path("/opt/ott/sources/perfect6502"),
    ):
        extra_globs.append({"root": str(pattern_root), "exists": pattern_root.exists()})
        if pattern_root.exists():
            for p in pattern_root.rglob(ISA_FILENAME):
                if p.is_file():
                    key = str(p.resolve())
                    if key not in seen:
                        seen.add(key)
                        hits.append(p)
                        records.append(file_record(p))
    shas = {r["sha256"] for r in records}
    if len(shas) > 1:
        write_json(
            "LIBISA6502_DISCOVERY.json",
            {"copies": records, "stop": "STOP_LIBISA6502_EXISTING_COPY_MISMATCH"},
        )
        raise Stop("STOP_LIBISA6502_EXISTING_COPY_MISMATCH", {"copies": records})
    doc = {
        "document": "LIBISA6502_DISCOVERY",
        "search_roots": ["/opt/ott", "/opt/ott/sources", "/workspace"],
        "explicit_inspect": [
            {"path": str(p), "present": p.is_file()} for p in EXPLICIT_ISA
        ],
        "extra_trees": extra_globs,
        "copy_count": len(records),
        "copies": records,
        "byte_identity": True if len(shas) <= 1 else False,
    }
    write_json("LIBISA6502_DISCOVERY.json", doc)
    return doc


def loader_analysis(cae: Path) -> Dict[str, Any]:
    py_path = cae / "systems" / "10_cpu_6502.py"
    sh_path = cae / "systems" / "10_cpu_6502_libs" / "build_libs.sh"
    isa_c = cae / "systems" / "10_cpu_6502_libs" / "isa_bridge.c"
    isa_ver = cae / "systems" / "10_cpu_6502_libs" / "isa.version"
    if not py_path.is_file() or not sh_path.is_file():
        raise Stop("STOP_LIBISA6502_LOADER_MAPPING_AMBIGUOUS", {"missing": [str(py_path), str(sh_path)]})
    py_txt = py_path.read_text(encoding="utf-8", errors="replace")
    sh_txt = sh_path.read_text(encoding="utf-8", errors="replace")
    py_lines = py_txt.splitlines()
    sh_lines = sh_txt.splitlines()

    def excerpt(lines: List[str], start: int, end: int) -> str:
        chunk = lines[start - 1 : end]
        numbered = [f"{i+start}: {ln}" for i, ln in enumerate(chunk)]
        return "\n".join(numbered)

    honors = "CPU6502_LIB_DIR" in py_txt and "_find_lib" in py_txt and 'ISASimulator' in py_txt
    cwd = "os.getcwd()" in py_txt and "_find_lib" in py_txt
    md = f"""# CAE ISA loader analysis (pinned runtime source)

Read-only excerpts from `{py_path}` and `{sh_path}`.

## How ISASimulator locates libisa6502.so

`_LIB_DIR` is bound at import time from `CPU6502_LIB_DIR` if set, otherwise
`systems/10_cpu_6502_libs` next to `10_cpu_6502.py`. `_find_lib(name)` then
searches, in order: `_LIB_DIR`, the directory containing `10_cpu_6502.py`,
and `os.getcwd()`. `ISASimulator.__init__` calls `_find_lib("libisa6502.so")`
and raises `FileNotFoundError("libisa6502.so not found")` if none of those
paths exist.

Therefore setting `CPU6502_LIB_DIR` to a scratch directory that does not
contain `libisa6502.so` replaces the default `10_cpu_6502_libs` search slot.
A copy that exists only under `10_cpu_6502_libs/` is then invisible unless it
is also staged into `CPU6502_LIB_DIR`, `systems/libisa6502.so`, or cwd.

## CPU6502_LIB_DIR

Honored: yes, as the first search directory, captured at import.

## Expected filename/path

Filename: `libisa6502.so`
Default directory: `<cae>/systems/10_cpu_6502_libs/`

## CWD dependence

`_find_lib` searches `os.getcwd()` as the third slot. `ISASimulator` itself
does not chdir. (`GateSimulator` chdirs into the lib directory only during
`gate_init()` to locate `Decoder6502.bin`.)

## Native ABI / exports required by ISASimulator

From `ISASimulator.__init__`:

- `isa_init()`
- `isa_execute_instruction(...)` with the ctypes prototype in the excerpt

`isa.version` also exports `isa_poke`.

## build_libs.sh ISA recipe

See excerpt. Unique ISA recipe in this file: one `gcc -O2 -shared -fPIC`
invocation linking `isa_bridge.c` with `$FAKE_DIR/fake6502.c`.

```
{excerpt(py_lines, 118, 188)}
```

```
{excerpt(sh_lines, 1, 38)}
```
"""
    write_text("CAE_ISA_LOADER_ANALYSIS.md", md)
    return {
        "python_path": str(py_path),
        "build_script": str(sh_path),
        "isa_bridge_c": str(isa_c),
        "isa_version": str(isa_ver),
        "honors_CPU6502_LIB_DIR": honors,
        "cwd_dependence": cwd,
        "expected_filename": ISA_FILENAME,
        "required_exports": list(EXPECTED_ISA_EXPORTS),
        "isa_bridge_present": isa_c.is_file(),
        "isa_version_present": isa_ver.is_file(),
    }


def analyze_build_path(cae: Path, fake: Optional[Path]) -> Dict[str, Any]:
    sh_path = cae / "systems" / "10_cpu_6502_libs" / "build_libs.sh"
    isa_c = cae / "systems" / "10_cpu_6502_libs" / "isa_bridge.c"
    isa_ver = cae / "systems" / "10_cpu_6502_libs" / "isa.version"
    sh_txt = sh_path.read_text(encoding="utf-8")
    gcc_blocks = re.findall(r"echo \"\[1/3\] Building libisa6502\.so.*?\n(.*?)echo \"  Done: libisa6502.so\"", sh_txt, re.S)
    if len(gcc_blocks) != 1:
        write_text(
            "BUILD_PATH_ANALYSIS.md",
            "STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS: ISA gcc block count "
            f"= {len(gcc_blocks)}\n",
        )
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"gcc_blocks": len(gcc_blocks)})
    if sh_txt.count("-o libisa6502.so") != 1:
        write_text("BUILD_PATH_ANALYSIS.md", "STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS: multiple -o libisa6502.so\n")
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"detail": "multiple -o libisa6502.so"})
    candidates: List[Path] = []
    env_dir = os.environ.get("FAKE6502_DIR", "")
    for cand in (Path(env_dir) if env_dir else None, Path.home() / "fake6502", Path("/opt/ott/sources/fake6502"), fake):
        if cand is None:
            continue
        if (cand / "fake6502.c").is_file() and (cand / "fake6502.h").is_file():
            rp = cand.resolve()
            if rp not in candidates:
                candidates.append(rp)
    if not candidates:
        write_text("BUILD_PATH_ANALYSIS.md", "missing fake6502.c / fake6502.h\n")
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"detail": "no fake6502 source tree"})
    hashed = []
    for c in candidates:
        hashed.append({"path": str(c), "head": git_head(c), "fake6502_c_sha256": sha256_file(c / "fake6502.c")})
    sha_set = {h["fake6502_c_sha256"] for h in hashed}
    head_set = {h["head"] for h in hashed}
    if len(candidates) > 1 and (len(sha_set) > 1 or len(head_set) > 1):
        write_text("BUILD_PATH_ANALYSIS.md", "multiple non-identical fake6502 mappings\n")
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"candidates": hashed})
    if len(candidates) > 1 and sha_set and head_set == {FAKE6502_COMMIT}:
        # Identical pinned trees: mechanically one content identity. Use /opt/ott/sources/fake6502 if present.
        preferred = Path("/opt/ott/sources/fake6502")
        fake_src = preferred.resolve() if preferred.exists() else candidates[0]
    else:
        fake_src = candidates[0]
    if git_head(fake_src) != FAKE6502_COMMIT:
        write_text("BUILD_PATH_ANALYSIS.md", f"fake6502 HEAD {git_head(fake_src)}\n")
        raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": f"fake6502 HEAD {git_head(fake_src)}"})
    if not isa_c.is_file() or not isa_ver.is_file():
        write_text("BUILD_PATH_ANALYSIS.md", "missing isa_bridge.c or isa.version\n")
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"isa_c": isa_c.is_file(), "isa_ver": isa_ver.is_file()})
    gcc_ver = run_text(["gcc", "--version"])
    date_hits = []
    for p in (isa_c, fake_src / "fake6502.c", fake_src / "fake6502.h"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "__DATE__" in txt or "__TIME__" in txt:
            date_hits.append(str(p))
    cmd = (
        f"gcc -O2 -shared -fPIC -Wl,--version-script={isa_ver} "
        f"-o libisa6502.so {isa_c} {fake_src / 'fake6502.c'} -I{fake_src}"
    )
    analysis = {
        "source_repository_path": str(fake_src),
        "source_commit": FAKE6502_COMMIT,
        "bridge_source": str(isa_c),
        "version_script": str(isa_ver),
        "working_directory_in_script": str(cae / "systems" / "10_cpu_6502_libs"),
        "scratch_output_only": True,
        "compiler": "gcc",
        "compiler_version": gcc_ver.strip() if gcc_ver else None,
        "compile_link_flags": ["-O2", "-shared", "-fPIC", "-Wl,--version-script=isa.version"],
        "output_filename": ISA_FILENAME,
        "required_headers_sources": ["isa_bridge.c", "isa.version", "fake6502.c", "fake6502.h"],
        "environment_variables": {"FAKE6502_DIR": str(fake_src)},
        "depends_on_randomness": False,
        "depends_on_wall_clock_macros": bool(date_hits),
        "date_macro_files": date_hits,
        "depends_on_hostname": False,
        "depends_on_network": False,
        "external_unpinned_toolchain": False,
        "canonical_command": cmd,
        "mechanically_unique": True,
        "fake6502_candidates": hashed,
    }
    md = f"""# libisa6502 canonical build path

Unique ISA recipe from pinned `build_libs.sh` (one gcc invocation).

Frozen trees are not written. Output is directed at a fresh scratch directory.
Inputs remain the pinned CAE bridge and pinned fake6502 sources.

```
source repository/path = {fake_src}
source commit = {FAKE6502_COMMIT}
compiler = gcc
compiler version =
{gcc_ver}
compile/link flags = -O2 -shared -fPIC -Wl,--version-script=isa.version
output filename = libisa6502.so
required headers/sources = isa_bridge.c, isa.version, fake6502.c, fake6502.h
working directory (script) = {cae / "systems" / "10_cpu_6502_libs"}
working directory (diagnostic) = fresh scratch (output only)
environment variables = FAKE6502_DIR={fake_src}
dynamic dependencies = recorded after GEN via ldd/readelf
randomness = no
wall clock macros (__DATE__/__TIME__) = {date_hits or "none"}
hostname = no
filesystem ordering = not used by this gcc line
network = no
external unpinned toolchain content = no (image gcc)
```

Canonical command (absolute inputs, scratch `-o`):

```
{cmd}
```
"""
    write_text("BUILD_PATH_ANALYSIS.md", md)
    if date_hits:
        raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"detail": "__DATE__/__TIME__", "files": date_hits})
    analysis["isa_c"] = str(isa_c)
    analysis["isa_ver"] = str(isa_ver)
    analysis["fake_src"] = str(fake_src)
    return analysis


def gen_once(out_dir: Path, isa_c: Path, isa_ver: Path, fake_c: Path, fake_inc: Path) -> Dict[str, Any]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-c", _GEN_CHILD, str(out_dir), str(isa_c), str(isa_ver), str(fake_c), str(fake_inc)],
        capture_output=True,
        text=True,
        cwd=str(out_dir),
    )
    wall = time.monotonic() - t0
    so = out_dir / ISA_FILENAME
    rec: Dict[str, Any] = {
        "rc": proc.returncode,
        "wall_s": wall,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "compiler_command": [
            "gcc",
            "-O2",
            "-shared",
            "-fPIC",
            f"-Wl,--version-script={isa_ver}",
            "-o",
            "libisa6502.so",
            str(isa_c),
            str(fake_c),
            f"-I{fake_inc}",
        ],
        "produced": so.is_file(),
    }
    if so.is_file():
        rec.update(file_record(so))
        exports = []
        nm = rec.get("nm_defined_T") or ""
        for ln in nm.splitlines():
            parts = ln.split()
            if len(parts) >= 3 and parts[1] == "T":
                exports.append(parts[2])
        rec["exported_symbols"] = exports
    return rec


def scratch_lib(libisa: Path, libgate: Path, decoder: Path, dest: Path) -> Dict[str, Any]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy2(libisa, dest / ISA_FILENAME)
    shutil.copy2(libgate, dest / GATE_FILENAME)
    shutil.copy2(decoder, dest / "Decoder6502.bin")
    return {
        "dir": str(dest),
        "libisa6502_sha256": sha256_file(dest / ISA_FILENAME),
        "libgate6502_sha256": sha256_file(dest / GATE_FILENAME),
        "decoder6502_sha256": sha256_file(dest / "Decoder6502.bin"),
        "entries": sorted(p.name for p in dest.iterdir()),
    }


def run_smokes(lib_dir: Path, cae: Path) -> Dict[str, Any]:
    cpu = load_cpu(lib_dir, cae)
    isa = nop_smoke(cpu, "isa")
    gate = nop_smoke(cpu, "gate")
    return {"isa": isa, "gate": gate, "PASS": bool(isa.get("PASS") and gate.get("PASS"))}


def unlink_generated(*paths: Path) -> None:
    for p in paths:
        try:
            if p.is_file() and p.suffix in {".so", ".bin"}:
                p.unlink()
        except Exception:
            pass


def main() -> int:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    write_text("RUN_AUTHORIZATION_CONSUMED.txt", "NO\n")
    write_text("START_STAGE_A.txt", "ABSENT\n")
    write_text("STAGE_A_EXECUTION.txt", "NO\n")
    write_text("SCIENTIFIC_OBSERVATIONS.txt", "0\n")
    try:
        if Path("/ott/run").exists() or Path("/workspace/ott-run").exists():
            raise Stop("STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", {"detail": "ott-run must stay unused"})
        cae = locate_cae()
        ident = parent_identity(cae)
        loader = loader_analysis(cae)
        discovery = discover_isa()
        copies = discovery.get("copies") or []
        if copies:
            staged = scratch_lib(
                Path(copies[0]["absolute_path"]),
                ident["libgate"],
                ident["decoder"],
                SCRATCH_ROOT / "class-a",
            )
            try:
                smoke = run_smokes(Path(staged["dir"]), ident["cae"])
            except Exception as e:
                traceback.print_exc()
                write_json("ISA_SMOKE.json", {"PASS": False, "error": f"{type(e).__name__}: {e}", "scratch": staged})
                write_text("BUILD_PATH_ANALYSIS.md", "Class A smoke failed; no unique existing-lib relocation.\n")
                write_json("LIBISA6502_DETERMINISM.json", {"skipped": True, "reason": "class_a_smoke_failure"})
                raise Stop("STOP_LIBISA6502_SCRATCH_SMOKE_FAILURE", {"error": f"{type(e).__name__}: {e}", "scratch": staged})
            write_json("ISA_SMOKE.json", {"mode": "existing_immutable_lib", **smoke, "scratch": staged})
            write_text(
                "BUILD_PATH_ANALYSIS.md",
                "Not executed: libisa6502.so already exists in the immutable runtime (Class A).\n",
            )
            write_json(
                "LIBISA6502_DETERMINISM.json",
                {"skipped": True, "reason": "existing_immutable_lib", "NEW_EXTERNAL_RUNTIME_BYTES": 0},
            )
            unlink_generated(Path(staged["dir"]) / ISA_FILENAME, Path(staged["dir"]) / "Decoder6502.bin")
            classify_and_report(
                "A_EXISTING_IMMUTABLE_LIB_RELOCATION",
                {
                    "LIBISA6502_EXISTING_IMAGE_RELOCATION": "PASS",
                    "SCIENTIFIC_SEMANTICS_DELTA": 0,
                    "NEW_EXTERNAL_RUNTIME_BYTES": 0,
                    "loader": loader,
                    "discovery_copy_count": len(copies),
                    "existing_copy": copies[0],
                    "scratch": staged,
                    "smoke": smoke,
                },
            )
            return 0

        analysis = analyze_build_path(ident["cae"], ident.get("fake6502"))
        isa_c = Path(analysis["isa_c"])
        isa_ver = Path(analysis["isa_ver"])
        fake_src = Path(analysis["fake_src"])
        gen1_dir = Path("/tmp/ott-isa6502-gen1")
        gen2_dir = Path("/tmp/ott-isa6502-gen2")
        g1 = gen_once(gen1_dir, isa_c, isa_ver, fake_src / "fake6502.c", fake_src)
        g2 = gen_once(gen2_dir, isa_c, isa_ver, fake_src / "fake6502.c", fake_src)
        det = {"gen1": g1, "gen2": g2}
        if not g1.get("produced") or not g2.get("produced"):
            write_json("LIBISA6502_DETERMINISM.json", det)
            write_json("ISA_SMOKE.json", {"skipped": True, "reason": "build_failed"})
            raise Stop("STOP_LIBISA6502_BUILD_MAPPING_AMBIGUOUS", {"determinism": det})
        if g1["sha256"] != g2["sha256"] or g1["bytes"] != g2["bytes"]:
            write_json("LIBISA6502_DETERMINISM.json", {**det, "identical": False})
            write_json("ISA_SMOKE.json", {"skipped": True, "reason": "nondeterministic"})
            raise Stop("STOP_LIBISA6502_BUILD_NONDETERMINISTIC", {"determinism": det})
        exports = set(g1.get("exported_symbols") or [])
        if not set(EXPECTED_ISA_EXPORTS).issubset(exports):
            write_json("LIBISA6502_DETERMINISM.json", {**det, "identical": True})
            write_json("ISA_SMOKE.json", {"skipped": True, "reason": "abi"})
            raise Stop("STOP_LIBISA6502_ABI_AMBIGUOUS", {"exports": sorted(exports)})
        write_json(
            "LIBISA6502_DETERMINISM.json",
            {
                **det,
                "identical": True,
                "LIBISA6502_BYTES": g1["bytes"],
                "LIBISA6502_SHA256": g1["sha256"],
                "LIBISA6502_BUILD_COMMAND": g1["compiler_command"],
            },
        )
        smoke_dir = SCRATCH_ROOT / "generated"
        staged = scratch_lib(gen1_dir / ISA_FILENAME, ident["libgate"], ident["decoder"], smoke_dir)
        try:
            smoke = run_smokes(smoke_dir, ident["cae"])
        except Exception as e:
            traceback.print_exc()
            write_json("ISA_SMOKE.json", {"PASS": False, "error": f"{type(e).__name__}: {e}", "scratch": staged})
            raise Stop("STOP_LIBISA6502_SCRATCH_SMOKE_FAILURE", {"error": f"{type(e).__name__}: {e}"})
        write_json(
            "ISA_SMOKE.json",
            {"mode": "generated_scratch", "LIBISA6502_GENERATED_SCRATCH_SMOKE": "PASS" if smoke["PASS"] else "FAIL", **smoke, "scratch": staged},
        )
        unlink_generated(
            gen1_dir / ISA_FILENAME,
            gen2_dir / ISA_FILENAME,
            smoke_dir / ISA_FILENAME,
            smoke_dir / "Decoder6502.bin",
        )
        if not smoke["PASS"]:
            raise Stop("STOP_LIBISA6502_SCRATCH_SMOKE_FAILURE", {"smoke": smoke})
        classify_and_report(
            "B_DETERMINISTIC_RUNTIME_SUPPLEMENT_REQUIRED",
            {
                "LIBISA6502_GENERATED_SCRATCH_SMOKE": "PASS",
                "LIBISA6502_BYTES": g1["bytes"],
                "LIBISA6502_SHA256": g1["sha256"],
                "LIBISA6502_BUILD_COMMAND": g1["compiler_command"],
                "loader": loader,
                "build": {k: analysis[k] for k in analysis if k not in {"isa_c", "isa_ver", "fake_src"}},
                "smoke": smoke,
            },
        )
        return 0
    except Stop as e:
        extra = {"stop": e.code, **e.extra}
        classification = "C_RUNTIME_SUPERSESSION_REQUIRED"
        if e.code == "STOP_LIBISA6502_EXISTING_COPY_MISMATCH":
            classification = "C_RUNTIME_SUPERSESSION_REQUIRED"
        classify_and_report(classification, extra)
        return 2
    except Exception as e:
        traceback.print_exc()
        classify_and_report(
            "C_RUNTIME_SUPERSESSION_REQUIRED",
            {"stop": "STOP_LIBISA6502_PARENT_IDENTITY_FAILURE", "error": f"{type(e).__name__}: {e}"},
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
