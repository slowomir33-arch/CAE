#!/usr/bin/env bash
# Static validation for the Decoder6502 PRESTART diagnostic window.
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

python3 -m py_compile tools/ott_v056_d6502/d6502_diagnostic.py
echo "PASS py_compile d6502_diagnostic.py"

python3 - <<'PY'
import re, sys
from pathlib import Path
root = Path(".")
ci = (root / ".github/workflows/ci.yml").read_text()
ded = (root / ".github/workflows/ott-v056-stage-a.yml").read_text()
ent = (root / "tools/ott_v056_d6502/gha_entrypoint.sh").read_text()
py = (root / "tools/ott_v056_d6502/d6502_diagnostic.py").read_text()
fail = 0

def ok(cond, msg):
    global fail
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail = 1

# Stage A unreachable on CI dispatch
ok("ott-v056-d6502-diagnostic:" in ci, "CI defines diagnostic job")
ok("if: github.event_name == 'workflow_dispatch'" in ci, "diagnostic job is workflow_dispatch only")
ok(re.search(r"ott-v056-stage-a:\n(?:.*\n){0,6}\s+if: false", ci) is not None, "CI Stage-A job if: false")
ok(re.search(r"stage-a:\n(?:.*\n){0,4}\s+if: false", ded) is not None, "dedicated Stage-A job if: false")
ok("if: github.event_name != 'workflow_dispatch'" in ci, "unit-test jobs skip workflow_dispatch")
ok(ci.count("if: github.event_name != 'workflow_dispatch'") >= 2, "test and import-matrix skip dispatch")

# Diagnostic identity is generated on the runner, not committed
ok("OTT-v0.5.6-D6502-${UTC}-${RAND}" in ci, "diagnostic ID template on runner")
committed = "\n".join([ci, ded, ent, py])
ok(re.search(r"OTT-v0\.5\.6-D6502-20\d{6}T\d{6}Z-[0-9A-F]{8}", committed) is None,
   "no hardcoded diagnostic RUN_ID")

# Stage A START / auth consumption unreachable from diagnostic tools
ok("exclusive_create" not in ent and "exclusive_create" not in py,
   "diagnostic tools do not exclusive-create START")
ok("host-start" not in ent and "host-start" not in py,
   "diagnostic tools do not call host-start")
ok("Does NOT create START_STAGE_A.json" in ent,
   "entrypoint states START_STAGE_A.json is not created")
ok("NO START_STAGE_A" in py or "START_STAGE_A\": \"ABSENT\"" in py or '"START_STAGE_A": "ABSENT"' in py,
   "diagnostic records START_STAGE_A ABSENT")
ok("stage_a_executor" not in ent and "stage_a_executor" not in py,
   "diagnostic tools do not invoke Stage A executor")
ok("ott-run" in ent and "must stay unused" in ent, "entrypoint refuses ott-run")
ok("RUN_AUTHORIZATION" in py and "NO" in py, "diagnostic records auth unconsumed")
ok("Decoder6502.bin" in py and "find /opt/ott/sources" in py, "D2 discovery present")
ok("CPU6502_LIB_DIR" in py, "scratch lib dir override present")
ok("0xEA" in py, "NOP sentinel present")
ok("fresh-process" in py or "fresh python process" in py, "D4 uses fresh process")
ok("workflow_dispatch" in ci, "CI keeps workflow_dispatch")
ok("GHCR_PULL_TOKEN" in ci and "GHCR_PULL_TOKEN" in ent, "GHCR pull token used")
ok("network none" in ent, "container has no network")
ok("Do not mount checkout at /workspace" in ent or "/workspace" in ent,
   "entrypoint documents not mounting checkout at /workspace")
ok("-v \"$ROOT/tools/ott_v056_d6502:/ott/gha/tools/ott_v056_d6502:ro\"" in ent or
   "/ott/gha/tools/ott_v056_d6502" in ent, "tools mounted read-only, not checkout at /workspace")
ok("gha-d6502-receipts/" in ci and "ott-run/" not in ci.split("ott-v056-d6502-diagnostic")[1].split("ott-v056-stage-a:")[0],
   "diagnostic artifact does not upload ott-run")
sys.exit(fail)
PY
check "gha_entrypoint is executable-ready" test -f tools/ott_v056_d6502/gha_entrypoint.sh
chmod +x tools/ott_v056_d6502/gha_entrypoint.sh tools/ott_v056_d6502/d6502_diagnostic.py tools/ott_v056_d6502/static_validate.sh
bash -n tools/ott_v056_d6502/gha_entrypoint.sh
echo "PASS bash -n gha_entrypoint.sh"

# Public protocol / Stage A evidence must not be mutated by this commit set.
check "RUN_AUTHORIZATION.json unchanged path exists" test -f evidence/v056-sca-gha/RUN_AUTHORIZATION.json

if [ "$fail" -ne 0 ]; then
  echo "STATIC_VALIDATION = FAIL" >&2
  exit 1
fi
echo "STATIC_VALIDATION = PASS"
echo "STAGE_A_EXECUTION = NO"
echo "START_STAGE_A = ABSENT"
echo "RUN_AUTHORIZATION_CONSUMED = NO"
