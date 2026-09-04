#!/usr/bin/env bash
# Static validation for the runtime-fingerprint PRESTART diagnostic window.
# Does not dispatch. Does not run Stage A.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
fail=0

python3 -m py_compile tools/ott_v056_rfp/rfp_diagnostic.py
echo "PASS py_compile rfp_diagnostic.py"
bash -n tools/ott_v056_rfp/gha_entrypoint.sh
echo "PASS bash -n gha_entrypoint.sh"

python3 - <<'PY'
import hashlib, json, re, sys
from pathlib import Path
root = Path(".")
ci = (root / ".github/workflows/ci.yml").read_text()
ded = (root / ".github/workflows/ott-v056-stage-a.yml").read_text()
ent = (root / "tools/ott_v056_rfp/gha_entrypoint.sh").read_text()
py = (root / "tools/ott_v056_rfp/rfp_diagnostic.py").read_text()
auth = (root / "evidence/v056-stage-a-reauthorization/RUN_AUTHORIZATION.json").read_bytes()
fail = 0

def ok(cond, msg):
    global fail
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail = 1

def job_if(text, job):
    m = re.search(rf"(?m)^  {re.escape(job)}:\n(?:.*\n)*?    if: (.+)\n", text)
    return m.group(1).strip() if m else None

ok(job_if(ci, "ott-v056-stage-a") == "false", "1 Stage A disabled")
ok(job_if(ci, "ott-v056-runtime-fingerprint-diagnostic") == "github.event_name == 'workflow_dispatch'",
   "2 RFP diagnostic is workflow_dispatch only")
ok(job_if(ci, "test") == "github.event_name != 'workflow_dispatch'", "2 unit tests skip dispatch")
ok(job_if(ci, "import-matrix") == "github.event_name != 'workflow_dispatch'", "2 import-matrix skip dispatch")
ok(all(job_if(ci, j) == "false" for j in (
    "ott-v056-libisa6502-diagnostic",
    "ott-v056-d6502-diagnostic",
    "ott-v056-d6502-supplement-freeze",
    "ott-v056-d6502-supplement-retrieve",
)), "2 other diagnostic/freeze jobs disabled")
ok(hashlib.sha256(auth).hexdigest() == "cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26",
   "3 generation-2 RUN_AUTHORIZATION byte-identical")
ok(json.loads(auth.decode()).get("consumed") is False, "3 consumed=false")
ok(not list(root.rglob("START_STAGE_A.json")), "4 no START_STAGE_A.json in tree")
ok("docker build" not in ent and "docker push" not in ent, "5 no OCI mutation commands")
ok("host-start" not in ent and "host-start" not in py, "6 no science START path")
ok("stage_a_executor" not in ent, "6 entrypoint does not invoke Stage A executor")
ok("exclusive_create" not in py and "host-start" not in py, "6 diagnostic python has no START exclusive-create")
ok("ott-run" in ent and "must stay unused" in ent, "6 entrypoint refuses ott-run")
ok(re.search(r"OTT-v0\.5\.6-RFP-20\d{6}T\d{6}Z-[0-9A-F]{8}", "\n".join([ci, ent, py])) is None,
   "no hardcoded diagnostic RUN_ID")
ok("OTT-v0.5.6-RFP-${UTC}-${RAND}" in ci, "diagnostic ID generated on runner")
ok("def _fingerprint_check()" in py, "D3 verbatim locator present")
ok("166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271" in py, "accepted FP root bound")
ok("8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd" in py, "accepted FP JSON SHA bound")
ok("A_EXISTING_IMMUTABLE_FINGERPRINT_RELOCATION" in py
   and "B_FINGERPRINT_NOT_EMBEDDED_AUDITOR_DECISION_REQUIRED" in py
   and "C_RUNTIME_FINGERPRINT_CONTRADICTION" in py, "exact classification labels")
ok("network none" in ent, "container has no network")
ok("--read-only" in ent, "container filesystem is read-only")
ok("/ott/gha/tools/ott_v056_rfp" in ent, "tools mounted read-only")
ok("ott-run/" not in ci.split("ott-v056-runtime-fingerprint-diagnostic")[1].split("ott-v056-stage-a:")[0],
   "diagnostic artifact does not upload ott-run")
ok(re.search(r"stage-a:\n(?:.*\n){0,4}\s+if: false", ded) is not None, "dedicated Stage-A job if: false")
sys.exit(fail)
PY
chmod +x tools/ott_v056_rfp/gha_entrypoint.sh tools/ott_v056_rfp/rfp_diagnostic.py tools/ott_v056_rfp/static_validate.sh
if [ "$fail" -ne 0 ]; then
  echo "STATIC_VALIDATION = FAIL" >&2
  exit 1
fi
echo "STATIC_VALIDATION = PASS"
echo "STAGE_A_EXECUTION = NO"
echo "START_STAGE_A = ABSENT"
echo "RUN_AUTHORIZATION_CONSUMED = NO"
echo "WORKFLOW_DISPATCH = NOT PERFORMED"
