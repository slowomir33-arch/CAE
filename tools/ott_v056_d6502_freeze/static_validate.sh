#!/usr/bin/env bash
# Static validation for the Decoder6502 immutable runtime supplement freeze.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 -m py_compile \
  tools/ott_v056_d6502_freeze/inimage_generate.py \
  tools/ott_v056_d6502_freeze/inimage_smoke.py \
  tools/ott_v056_d6502_freeze/assemble_supplement.py \
  tools/ott_v056_d6502_freeze/verify_extracted.py
echo "PASS py_compile freeze tools"
bash -n tools/ott_v056_d6502_freeze/gha_freeze.sh
bash -n tools/ott_v056_d6502_freeze/gha_retrieve.sh
echo "PASS bash -n freeze shells"
python3 - <<'PY'
import re, sys
from pathlib import Path
root = Path(".")
ci = (root / ".github/workflows/ci.yml").read_text()
ded = (root / ".github/workflows/ott-v056-stage-a.yml").read_text()
freeze = (root / "tools/ott_v056_d6502_freeze/gha_freeze.sh").read_text()
retr = (root / "tools/ott_v056_d6502_freeze/gha_retrieve.sh").read_text()
df = (root / "tools/ott_v056_d6502_freeze/Dockerfile.scratch").read_text()
fail = 0

def ok(cond, msg):
    global fail
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail = 1

ok("ott-v056-d6502-supplement-freeze:" in ci, "CI defines freeze job")
ok("ott-v056-d6502-supplement-retrieve:" in ci, "CI defines retrieve job")
ok("packages: write" in ci, "freeze job can write packages")
ok("needs: ott-v056-d6502-supplement-freeze" in ci, "retrieve needs freeze")
ok(re.search(r"ott-v056-d6502-diagnostic:\n(?:.*\n){0,4}\s+if: false", ci) is not None, "diagnostic if: false")
ok(re.search(r"ott-v056-stage-a:\n(?:.*\n){0,6}\s+if: false", ci) is not None, "CI Stage-A if: false")
ok(re.search(r"stage-a:\n(?:.*\n){0,4}\s+if: false", ded) is not None, "dedicated Stage-A if: false")
ok("if: github.event_name != 'workflow_dispatch'" in ci, "unit tests skip dispatch")
ok("OTT-v0.5.6-D6502F-${UTC}-${RAND}" in ci, "freeze ID generated on runner")
blob = ci + freeze + retr
ok(re.search(r"OTT-v0\.5\.6-D6502F-20\d{6}T\d{6}Z-[0-9A-F]{8}", blob) is None, "no hardcoded freeze RUN_ID")
ok("exclusive_create" not in freeze and "exclusive_create" not in retr, "no exclusive START")
ok("stage_a_executor" not in freeze and "stage_a_executor" not in retr, "no Stage A executor")
ok("Does NOT create START_STAGE_A.json" in freeze, "freeze states no START")
ok("FROM scratch" in df, "minimal scratch image")
ok("latest" not in freeze.split("STAGING_TAG")[1][:400] if "STAGING_TAG" in freeze else False, "staging tag is freeze id")
ok("cae-ott-v056-d6502-supplement" in freeze and "cae-ott-v056-d6502-supplement" in retr, "target GHCR package")
blob_tools = freeze + retr + (root / "tools/ott_v056_d6502_freeze/assemble_supplement.py").read_text() + (root / "tools/ott_v056_d6502_freeze/inimage_generate.py").read_text()
ok("d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62" in blob_tools, "canonical decoder sha")
ok("ott-run" in freeze and "/workspace" in freeze, "refuses Stage A run dir / does not mount checkout at /workspace")
ok("GITHUB_TOKEN" in freeze and "STOP_D6502_SUPPLEMENT_GHCR_PUSH_UNAVAILABLE" in freeze, "push uses GITHUB_TOKEN only")
ok("if: github.event_name == 'workflow_dispatch'" in ci, "freeze is dispatch only")
ok("GHCR_PULL_TOKEN" in freeze and "GHCR_PULL_TOKEN" in retr, "base runtime pull token")
ok("INDEPENDENT_SUPPLEMENT_RETRIEVAL" in retr, "independent retrieval receipts")
sys.exit(fail)
PY
chmod +x tools/ott_v056_d6502_freeze/*.sh tools/ott_v056_d6502_freeze/*.py
test -f evidence/v056-sca-gha/RUN_AUTHORIZATION.json
echo "STATIC_VALIDATION = PASS"
echo "STAGE_A_EXECUTION = NO"
echo "START_STAGE_A = ABSENT"
echo "RUN_AUTHORIZATION_CONSUMED = NO"
