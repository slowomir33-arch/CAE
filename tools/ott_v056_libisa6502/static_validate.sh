#!/usr/bin/env bash
# Static validation for the libisa6502 PRESTART diagnostic window.
# Does not dispatch. Does not run Stage A.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
fail=0
check() {
  local msg="$1"
  shift
  if "$@"; then
    echo "PASS $msg"
  else
    echo "FAIL $msg" >&2
    fail=1
  fi
}

python3 -m py_compile tools/ott_v056_libisa6502/libisa6502_diagnostic.py
echo "PASS py_compile libisa6502_diagnostic.py"
bash -n tools/ott_v056_libisa6502/gha_entrypoint.sh
echo "PASS bash -n gha_entrypoint.sh"

python3 - <<'PY'
import hashlib, json, re, sys
from pathlib import Path
root = Path(".")
ci = (root / ".github/workflows/ci.yml").read_text()
ded = (root / ".github/workflows/ott-v056-stage-a.yml").read_text()
ent = (root / "tools/ott_v056_libisa6502/gha_entrypoint.sh").read_text()
py = (root / "tools/ott_v056_libisa6502/libisa6502_diagnostic.py").read_text()
auth_new = (root / "evidence/v056-stage-a-reauthorization/RUN_AUTHORIZATION.json").read_bytes()
auth_old = (root / "evidence/v056-sca-gha/RUN_AUTHORIZATION.json").read_bytes()
fail = 0

def ok(cond, msg):
    global fail
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail = 1

def job_if(text, job):
    m = re.search(rf"(?m)^  {re.escape(job)}:\n(?:.*\n)*?    if: (.+)\n", text)
    return m.group(1).strip() if m else None

ok("ott-v056-libisa6502-diagnostic:" in ci, "CI defines libisa6502 diagnostic job")
ok(job_if(ci, "ott-v056-libisa6502-diagnostic") == "github.event_name == 'workflow_dispatch'",
   "libisa6502 diagnostic is workflow_dispatch only")
ok(job_if(ci, "ott-v056-stage-a") == "false", "CI Stage-A job if: false")
ok(job_if(ci, "ott-v056-d6502-diagnostic") == "false", "d6502 diagnostic if: false")
ok(job_if(ci, "ott-v056-d6502-supplement-freeze") == "false", "freeze if: false")
ok(job_if(ci, "ott-v056-d6502-supplement-retrieve") == "false", "retrieve if: false")
ok(re.search(r"stage-a:\n(?:.*\n){0,4}\s+if: false", ded) is not None, "dedicated Stage-A job if: false")
ok("if: github.event_name != 'workflow_dispatch'" in ci, "unit-test jobs skip workflow_dispatch")
ok("OTT-v0.5.6-ISA6502-${UTC}-${RAND}" in ci, "diagnostic ID template on runner")
committed = "\n".join([ci, ded, ent, py])
ok(re.search(r"OTT-v0\.5\.6-ISA6502-20\d{6}T\d{6}Z-[0-9A-F]{8}", committed) is None,
   "no hardcoded diagnostic RUN_ID")
ok("exclusive_create" not in ent and "exclusive_create" not in py,
   "diagnostic tools do not exclusive-create START")
ok("host-start" not in ent and "host-start" not in py, "diagnostic tools do not call host-start")
ok("Does NOT create START_STAGE_A.json" in ent, "entrypoint states START_STAGE_A.json is not created")
ok("stage_a_executor" not in ent and "stage_a_executor" not in py,
   "diagnostic tools do not invoke Stage A executor")
ok("ott-run" in ent and "must stay unused" in ent, "entrypoint refuses ott-run")
ok("CPU6502_LIB_DIR" in py, "scratch lib dir override present")
ok("0xEA" in py, "NOP sentinel present")
ok("libisa6502.so" in py and "find" in py, "D1 discovery present")
ok("isa_bridge.c" in py and "build_libs.sh" in py, "D2/D3 build path present")
ok("_GEN_CHILD" in py, "D4 uses fresh process")
ok("network none" in ent, "container has no network")
ok("/ott/gha/tools/ott_v056_libisa6502" in ent, "tools mounted read-only")
ok("Do not mount the GHA checkout at /workspace" in ent, "checkout not mounted at /workspace")
ok("gha-isa6502-receipts/" in ci, "diagnostic artifact path present")
ok("ott-run/" not in ci.split("ott-v056-libisa6502-diagnostic")[1].split("ott-v056-stage-a:")[0],
   "diagnostic artifact does not upload ott-run")
ok("docker pull \"$SUPPLEMENT_REF\"" in ent, "supplement pulled by digest")
ok("docker build" not in ent, "no docker build in diagnostic entrypoint")
ok("cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26" == hashlib.sha256(auth_new).hexdigest(),
   "generation-2 authorization bytes unchanged")
ok("4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358" == hashlib.sha256(auth_old).hexdigest(),
   "old authorization bytes unchanged")
ok(json.loads(auth_new.decode()).get("consumed") is False, "generation-2 consumed=false")
ok(json.loads(auth_new.decode()).get("start_stage_a") == "ABSENT", "generation-2 start_stage_a ABSENT")
ok(not list(root.rglob("START_STAGE_A.json")), "no START_STAGE_A.json in tree")
ok("A_EXISTING_IMMUTABLE_LIB_RELOCATION" in py and "B_DETERMINISTIC_RUNTIME_SUPPLEMENT_REQUIRED" in py
   and "C_RUNTIME_SUPERSESSION_REQUIRED" in py, "exact classification labels present")
sys.exit(fail)
PY
check "gha_entrypoint exists" test -f tools/ott_v056_libisa6502/gha_entrypoint.sh
chmod +x tools/ott_v056_libisa6502/gha_entrypoint.sh tools/ott_v056_libisa6502/libisa6502_diagnostic.py tools/ott_v056_libisa6502/static_validate.sh

if [ "$fail" -ne 0 ]; then
  echo "STATIC_VALIDATION = FAIL" >&2
  exit 1
fi
echo "STATIC_VALIDATION = PASS"
echo "STAGE_A_EXECUTION = NO"
echo "START_STAGE_A = ABSENT"
echo "RUN_AUTHORIZATION_CONSUMED = NO"
echo "SCIENTIFIC_OBSERVATIONS = 0"
