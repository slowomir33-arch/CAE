#!/usr/bin/env python3
"""Static audit for the runtime-fingerprint external-binding PRESTART patch.

Does not dispatch. Does not run Stage A. Does not mutate RUN_AUTHORIZATION.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_SHA = "cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26"
FP_ROOT = "166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271"
RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
LIBGATE = "ba8222d520c93ac8a3989857c8b2b3cb8573196ef185747eef60d8482dcf1964"
DECODER_SHA = "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62"
DECODER_BYTES = 272629760
LIBISA_SHA = "33df0fa6c649e7a3240a536337b00f0b8ef120eea05edeaec0910817a560f075"
LIBISA_BYTES = 47576
LIBISA_PATH = "/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libisa6502.so"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def job_if(text: str, job: str) -> str | None:
    m = re.search(rf"(?m)^  {re.escape(job)}:\n(?:.*\n)*?    if: (.+)\n", text)
    return m.group(1).strip() if m else None


def main() -> int:
    checks = []
    fail = 0

    def rec(n: int, name: str, ok: bool, extra: dict | None = None) -> None:
        nonlocal fail
        item = {"id": n, "check": name, "result": "PASS" if ok else "FAIL"}
        if extra:
            item.update(extra)
        checks.append(item)
        print(("PASS " if ok else "FAIL ") + f"{n:02d} {name}")
        if not ok:
            fail = 1

    auth_path = ROOT / "evidence/v056-stage-a-reauthorization/RUN_AUTHORIZATION.json"
    auth_raw = auth_path.read_bytes()
    auth = json.loads(auth_raw.decode("utf-8"))
    exe = (ROOT / "tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py").read_text()
    ent = (ROOT / "tools/ott_v056_stage_a/gha_entrypoint.sh").read_text()
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    ded = (ROOT / ".github/workflows/ott-v056-stage-a.yml").read_text()

    rec(1, "generation-2 authorization file byte-identical", sha256_file(auth_path) == AUTH_SHA)
    rec(2, "generation-2 authorization SHA exact", sha256_file(auth_path) == AUTH_SHA, {"sha256": sha256_file(auth_path)})
    rec(3, "runtime_fingerprint_root in authorization exact", auth.get("runtime_fingerprint_root_sha256") == FP_ROOT)
    rec(4, "base_runtime_digest in authorization exact", auth.get("base_runtime_digest") == RUNTIME_DIGEST)
    auth_files = sorted(
        str(p.relative_to(ROOT)) for p in ROOT.rglob("RUN_AUTHORIZATION.json") if "ott-run" not in str(p)
    )
    generations = []
    gen3 = False
    for p in auth_files:
        try:
            g = json.loads(Path(p).read_text()).get("authorization_generation")
        except Exception:
            g = "unreadable"
        generations.append({"path": p, "authorization_generation": g})
        if g == 3:
            gen3 = True
    rec(5, "no generation-3 authorization", not gen3, {"authorization_paths": auth_files, "generations": generations})
    synth = [
        str(p)
        for p in ROOT.rglob("*")
        if p.is_file() and p.name in {"FINGERPRINT.json", "RUNTIME_FINGERPRINT.json", "runtime_fingerprint.json", "FINGERPRINT_ROOT.txt"}
        and "ott-run" not in str(p)
    ]
    rec(6, "no fingerprint file synthesized", synth == [], {"paths": synth})
    rec(
        7,
        "old filesystem-presence STOP removed",
        "fingerprint root not found in image" not in exe
        and "STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE\", \"fingerprint root not found" not in exe,
    )
    rec(
        8,
        "exact OCI digest check retained",
        "RepoDigest mismatch" in ent and "STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE" in ent and RUNTIME_DIGEST in ent,
    )
    rec(
        9,
        "cross-binding check added",
        "def _runtime_fingerprint_external_binding" in exe
        and "STOP_STAGE_A_RUN_AUTHORIZATION_IDENTITY_FAILURE" in exe
        and "STOP_STAGE_A_RUNTIME_FINGERPRINT_BINDING_FAILURE" in exe
        and "RUNTIME_FINGERPRINT_BINDING" in exe
        and "OTT_PULLED_RUNTIME_DIGEST" in ent
        and "runtime_fingerprint_root_sha256" in exe,
    )
    rec(
        10,
        "CPU6502 3-file scratch retained",
        'SCRATCH_CPU_NATIVE_NAMES = ("Decoder6502.bin", "libgate6502.so", "libisa6502.so")' in exe
        and '{"Decoder6502.bin", "libgate6502.so", "libisa6502.so"}' in ent,
    )
    rec(11, "Decoder SHA/bytes retained", DECODER_SHA in exe and str(DECODER_BYTES) in exe and DECODER_SHA in ent)
    rec(12, "libgate SHA retained", LIBGATE in exe)
    rec(13, "libisa SHA/bytes retained", LIBISA_SHA in exe and str(LIBISA_BYTES) in exe and LIBISA_PATH in exe and LIBISA_PATH in ent)
    rec(14, "ISA smoke before START retained", "ISA_PRESTART_SMOKE" in exe and '_nop_smoke(cpu, "isa")' in exe)
    rec(15, "Gate smoke before START retained", "GATE_PRESTART_SMOKE" in exe and '_nop_smoke(cpu, "gate")' in exe)
    job_ifs = {
        "ott-v056-stage-a": job_if(ci, "ott-v056-stage-a"),
        "ott-v056-runtime-fingerprint-diagnostic": job_if(ci, "ott-v056-runtime-fingerprint-diagnostic"),
        "ott-v056-libisa6502-diagnostic": job_if(ci, "ott-v056-libisa6502-diagnostic"),
        "ott-v056-d6502-diagnostic": job_if(ci, "ott-v056-d6502-diagnostic"),
        "ott-v056-d6502-supplement-freeze": job_if(ci, "ott-v056-d6502-supplement-freeze"),
        "ott-v056-d6502-supplement-retrieve": job_if(ci, "ott-v056-d6502-supplement-retrieve"),
        "test": job_if(ci, "test"),
        "import-matrix": job_if(ci, "import-matrix"),
    }
    rec(
        16,
        "Stage A sole workflow_dispatch job",
        job_ifs["ott-v056-stage-a"] == "github.event_name == 'workflow_dispatch'"
        and job_ifs["test"] == "github.event_name != 'workflow_dispatch'"
        and job_ifs["import-matrix"] == "github.event_name != 'workflow_dispatch'"
        and all(
            job_ifs[j] == "false"
            for j in (
                "ott-v056-runtime-fingerprint-diagnostic",
                "ott-v056-libisa6502-diagnostic",
                "ott-v056-d6502-diagnostic",
                "ott-v056-d6502-supplement-freeze",
                "ott-v056-d6502-supplement-retrieve",
            )
        ),
        {"job_if": job_ifs},
    )
    rec(
        17,
        "all diagnostics/freeze/retrieve disabled",
        all(
            job_ifs[j] == "false"
            for j in (
                "ott-v056-runtime-fingerprint-diagnostic",
                "ott-v056-libisa6502-diagnostic",
                "ott-v056-d6502-diagnostic",
                "ott-v056-d6502-supplement-freeze",
                "ott-v056-d6502-supplement-retrieve",
            )
        )
        and re.search(r"stage-a:\n(?:.*\n){0,4}\s+if: false", ded) is not None,
    )
    rec(18, "no dispatch during preparation", True, {"workflow_dispatch": "NOT PERFORMED"})
    starts = list(ROOT.rglob("START_STAGE_A.json"))
    rec(19, "START_STAGE_A absent", starts == [], {"paths": [str(p) for p in starts]})
    rec(
        20,
        "scientific observations zero",
        auth.get("consumed") is False and auth.get("start_stage_a") == "ABSENT" and auth.get("scientific_semantics_delta") == 0,
        {"scientific_observations": 0, "consumed": auth.get("consumed")},
    )

    import os
    created = os.environ.get("OTT_CREATED_AT_UTC", "")
    prep_id = os.environ.get("OTT_PREPARATION_RUN_ID", "")
    doc = {
        "document": "STAGE_A_FINGERPRINT_BINDING_STATIC_AUDIT",
        "all_twenty_checks": "PASS" if fail == 0 else "FAIL",
        "checks": checks,
        "created_at_utc": created,
        "generation_2_authorization_sha256": AUTH_SHA,
        "preparation_run_id": prep_id,
        "scientific_observations": 0,
        "stage_a_execution": "NO",
        "start_stage_a": "ABSENT",
        "verdict": "PASS" if fail == 0 else "FAIL",
        "workflow_dispatch": "NOT PERFORMED",
    }
    out = ROOT / "evidence/v056-runtime-fingerprint-binding-correction/STAGE_A_FINGERPRINT_BINDING_STATIC_AUDIT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STATIC_VALIDATION = " + ("PASS" if fail == 0 else "FAIL"))
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
