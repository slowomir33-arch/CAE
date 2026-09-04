#!/usr/bin/env bash
# Independent retrieval of the Decoder6502 supplement on a fresh GHA runner.
# Does NOT use the freeze build workspace/container. Does NOT run Stage A.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"
TOOLS="$ROOT/tools/ott_v056_d6502_freeze"
FREEZE_ID="${OTT_FREEZE_ID:?}"
DIGEST="${OTT_SUPPLEMENT_DIGEST:?}"
CONTENT_ROOT="${OTT_CONTENT_ROOT:?}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
SUPPLEMENT_REPO="ghcr.io/slowomir33-arch/cae-ott-v056-d6502-supplement"
SUPPLEMENT_REF="${SUPPLEMENT_REPO}@${DIGEST}"

RECEIPTS="$ROOT/gha-d6502f-retrieve"
EVIDENCE="$ROOT/evidence/v056-d6502-supplement-freeze"
EXTRACT="$ROOT/d6502f-indep-extract"
SMOKE_LIB="$ROOT/d6502f-indep-smoke-lib"
mkdir -p "$RECEIPTS" "$EVIDENCE" "$EXTRACT" "$SMOKE_LIB"

echo "$FREEZE_ID" > "$RECEIPTS/FREEZE_RUN_ID.txt"
echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
echo "NO" > "$RECEIPTS/STAGE_A_EXECUTION.txt"

stop() {
  local code="$1"
  echo "$code" | tee "$RECEIPTS/FREEZE_STOP.txt" >&2
  echo "STOP" > "$RECEIPTS/D6502_RUNTIME_SUPPLEMENT_FREEZE.txt"
  exit 1
}

if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to proceed: ott-run exists" >&2
  exit 1
fi
if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
case "$DIGEST" in
  sha256:*) ;;
  *) stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE ;;
esac

# Pull base runtime
AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_PULL_AUTH_MODE.txt"
if [ -z "${PULL_TOKEN:-}" ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
export GHCR_PULL_TOKEN=""
if [ "$LOGIN_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
docker pull "$RUNTIME_REF"
PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF")"
PULLED_DIGEST="${PULLED_REF##*@}"
if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
docker logout ghcr.io >/dev/null 2>&1 || true

# Pull supplement by digest with repository GITHUB_TOKEN
if [ -z "${GITHUB_TOKEN:-}" ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
set +e
printf '%s' "$GITHUB_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
SUP_LOGIN_RC=$?
set -e
if [ "$SUP_LOGIN_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
set +e
docker pull "$SUPPLEMENT_REF"
SUP_PULL_RC=$?
set -e
if [ "$SUP_PULL_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi
GOT_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$SUPPLEMENT_REF" 2>/dev/null || true)"
GOT_DIGEST="${GOT_REF##*@}"
echo "required=$DIGEST pulled=$GOT_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_SUPPLEMENT.txt"
if [ "$GOT_DIGEST" != "$DIGEST" ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi

CID="$(docker create --platform linux/amd64 "$SUPPLEMENT_REF" /bin/true)"
docker cp "$CID:/ott-supplement/." "$EXTRACT/"
docker rm "$CID" >/dev/null
COMPUTED_ROOT="$(python3 "$TOOLS/verify_extracted.py" "$EXTRACT" "$CONTENT_ROOT")"
echo "$COMPUTED_ROOT" > "$RECEIPTS/SUPPLEMENT_CONTENT_ROOT_SHA256.txt"
echo "$DIGEST" > "$RECEIPTS/SUPPLEMENT_OCI_DIGEST.txt"
echo "$SUPPLEMENT_REF" > "$RECEIPTS/SUPPLEMENT_OCI_REF.txt"
cp -a "$EXTRACT/SUPPLEMENT_IDENTITY.json" "$RECEIPTS/SUPPLEMENT_IDENTITY.json"
cp -a "$EXTRACT/SUPPLEMENT_MANIFEST.sha256" "$RECEIPTS/SUPPLEMENT_MANIFEST.sha256"

# Independent smoke with retrieved payload + retrieved base libgate
BASE_CID="$(docker create "$RUNTIME_REF")"
docker cp "$BASE_CID:/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libgate6502.so" "$SMOKE_LIB/libgate6502.so"
docker rm "$BASE_CID" >/dev/null
cp -a "$EXTRACT/Decoder6502.bin" "$SMOKE_LIB/Decoder6502.bin"
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e CPU6502_LIB_DIR=/tmp/ott-d6502-smoke/lib \
  -e OTT_RECEIPTS_DIR=/ott/receipts \
  -e OTT_SMOKE_OUT=INDEPENDENT_GATESIMULATOR_SMOKE.json \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$SMOKE_LIB:/tmp/ott-d6502-smoke/lib:ro" \
  -v "$TOOLS:/ott/gha/tools/ott_v056_d6502_freeze:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_d6502_freeze/inimage_smoke.py
SMOKE_RC=$?
set -e
if [ "$SMOKE_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_RETRIEVAL_FAILURE
fi

python3 - <<PY
import json, os, time
from pathlib import Path
receipts = Path("$RECEIPTS")
smoke = json.loads((receipts / "INDEPENDENT_GATESIMULATOR_SMOKE.json").read_text())
ident = json.loads((receipts / "SUPPLEMENT_IDENTITY.json").read_text())
freeze_id = "$FREEZE_ID"
digest = "$DIGEST"
root = "$COMPUTED_ROOT"
doc = {
  "INDEPENDENT_SUPPLEMENT_RETRIEVAL": "PASS",
  "INDEPENDENT_GATESIMULATOR_SMOKE": "PASS",
  "supplement_oci_digest": digest,
  "supplement_oci_ref": "$SUPPLEMENT_REF",
  "content_root": root,
  "decoder_bytes": 272629760,
  "decoder_sha256": "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62",
  "smoke": smoke,
  "identity_asset_sha256": ident.get("asset_sha256"),
}
receipts.joinpath("INDEPENDENT_RETRIEVAL.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
auth = {
  "document": "AUTHORIZATION_STATE",
  "RUN_AUTHORIZATION_SHA256": "4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358",
  "RUN_AUTHORIZATION_CONSUMED": "NO",
  "START_STAGE_A": "ABSENT",
  "OLD_RUN_AUTHORIZATION_STATUS": "UNCONSUMED_BUT_PENDING_SUPERSESSION",
  "STAGE_A_EXECUTION": "NO",
  "SCIENTIFIC_OBSERVATIONS": 0,
}
receipts.joinpath("AUTHORIZATION_STATE.json").write_text(json.dumps(auth, indent=2, sort_keys=True) + "\n")
created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
report = f"""# OTT v0.5.6 — DECODER6502 IMMUTABLE RUNTIME SUPPLEMENT FREEZE

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: DECODER6502_RUNTIME_SUPPLEMENT_FREEZE
RUN_ID: {freeze_id}
MESSAGE_ID: {freeze_id}-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: {created}
AGENT: Cursor/GitHub Actions Decoder6502 supplement freeze
PARENT_DIAGNOSTIC_RUN_ID: OTT-v0.5.6-D6502-20260904T112609Z-5B452FB6
PARENT_GITHUB_RUN_ID: 33867920935
BASE_RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
DECODER6502_SHA256: d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62
RUN_AUTHORIZATION_SHA256: 4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358
END_OTT_REPORT_SIGNATURE

```
D6502_RUNTIME_SUPPLEMENT_FREEZE = PASS

BASE_RUNTIME_DIGEST =
sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8

DECODER6502_SHA256 =
d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62

DECODER6502_BYTES = 272629760

DECODER6502_SUPPLEMENT_OCI_DIGEST =
{digest}

DECODER6502_SUPPLEMENT_OCI_REF =
ghcr.io/slowomir33-arch/cae-ott-v056-d6502-supplement@{digest}

SUPPLEMENT_CONTENT_ROOT_SHA256 =
{root}

LOCAL_GATESIMULATOR_SMOKE = PASS
INDEPENDENT_SUPPLEMENT_RETRIEVAL = PASS
INDEPENDENT_GATESIMULATOR_SMOKE = PASS

SCIENTIFIC_SEMANTICS_DELTA = 0
SCIENTIFIC_OBSERVATIONS = 0

RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT

OLD_RUN_AUTHORIZATION_STATUS =
UNCONSUMED_BUT_PENDING_SUPERSESSION

STAGE_A_EXECUTION = NO
```
"""
receipts.joinpath("D6502_SUPPLEMENT_FREEZE_REPORT.md").write_text(report)
receipts.joinpath("D6502_RUNTIME_SUPPLEMENT_FREEZE.txt").write_text("PASS\n")
print(report)
PY

rm -f "$EXTRACT/Decoder6502.bin" "$SMOKE_LIB/Decoder6502.bin"
shopt -s nullglob
for f in "$RECEIPTS"/*.json "$RECEIPTS"/*.md "$RECEIPTS"/*.txt "$RECEIPTS"/*.sha256; do
  cp -a "$f" "$EVIDENCE/$(basename "$f")"
done
find "$EVIDENCE" "$RECEIPTS" "$EXTRACT" "$SMOKE_LIB" -type f \( -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to leave ott-run behind" >&2
  exit 1
fi
echo "INDEPENDENT_RETRIEVAL_PASS"
exit 0
