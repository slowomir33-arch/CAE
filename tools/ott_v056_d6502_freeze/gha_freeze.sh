#!/usr/bin/env bash
# Decoder6502 immutable runtime supplement freeze — host entrypoint.
# Does NOT create START_STAGE_A.json and does NOT consume RUN_AUTHORIZATION.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"
TOOLS="$ROOT/tools/ott_v056_d6502_freeze"
FREEZE_ID="${OTT_FREEZE_ID:?OTT_FREEZE_ID must be injected by workflow identity step}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
SUPPLEMENT_REPO="ghcr.io/slowomir33-arch/cae-ott-v056-d6502-supplement"
STAGING_TAG="${SUPPLEMENT_REPO}:${FREEZE_ID}"

RECEIPTS="$ROOT/gha-d6502f-receipts"
EVIDENCE="$ROOT/evidence/v056-d6502-supplement-freeze"
OUT="$ROOT/d6502f-out"
CTX="$ROOT/d6502f-context"
EXTRACT="$ROOT/d6502f-extracted"
SMOKE_LIB="$ROOT/d6502f-smoke-lib"
mkdir -p "$RECEIPTS" "$EVIDENCE" "$OUT"

echo "$FREEZE_ID" > "$RECEIPTS/FREEZE_RUN_ID.txt"
echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
echo "NO" > "$RECEIPTS/STAGE_A_EXECUTION.txt"
echo "UNCONSUMED_BUT_PENDING_SUPERSESSION" > "$RECEIPTS/OLD_RUN_AUTHORIZATION_STATUS.txt"

if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to proceed: ott-run exists; Stage A path must stay unused" >&2
  exit 1
fi
if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  echo "STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE runner" >&2
  exit 1
fi

stop() {
  local code="$1"
  echo "$code" | tee "$RECEIPTS/FREEZE_STOP.txt" >&2
  echo "STOP" > "$RECEIPTS/D6502_RUNTIME_SUPPLEMENT_FREEZE.txt"
  exit 1
}

# --- pull base runtime (GHCR_PULL_TOKEN if present; else GITHUB_TOKEN) ---
AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_PULL_AUTH_MODE.txt"
if [ -z "${PULL_TOKEN:-}" ]; then
  stop STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE
fi
set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
export GHCR_PULL_TOKEN=""
if [ "$LOGIN_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE
fi
docker pull "$RUNTIME_REF"
PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF")"
PULLED_DIGEST="${PULLED_REF##*@}"
echo "PULLED_DIGEST=$PULLED_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_BASE.txt"
if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  stop STOP_D6502_SUPPLEMENT_PARENT_IDENTITY_FAILURE
fi
docker logout ghcr.io >/dev/null 2>&1 || true

# Do not mount checkout at /workspace. Do not mount ott-run.
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e OTT_FREEZE_ID="$FREEZE_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_RECEIPTS_DIR=/ott/receipts \
  -e OTT_OUT_DIR=/ott/out \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$OUT:/ott/out" \
  -v "$TOOLS:/ott/gha/tools/ott_v056_d6502_freeze:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_d6502_freeze/inimage_generate.py
GEN_RC=$?
set -e
if [ "$GEN_RC" -ne 0 ]; then
  if [ -f "$RECEIPTS/FREEZE_STOP.txt" ]; then
    stop "$(tr -d '\n' < "$RECEIPTS/FREEZE_STOP.txt")"
  fi
  stop STOP_D6502_SUPPLEMENT_REGENERATION_MISMATCH
fi

python3 "$TOOLS/assemble_supplement.py" "$CTX" "$OUT/Decoder6502.bin" "$TOOLS/README.runtime-supplement.txt" \
  | tee "$RECEIPTS/SUPPLEMENT_CONTENT_ROOT_SHA256.txt"
CONTENT_ROOT="$(tr -d '\n' < "$RECEIPTS/SUPPLEMENT_CONTENT_ROOT_SHA256.txt")"
cp -a "$CTX/SUPPLEMENT_IDENTITY.json" "$RECEIPTS/SUPPLEMENT_IDENTITY.json"
cp -a "$CTX/SUPPLEMENT_MANIFEST.sha256" "$RECEIPTS/SUPPLEMENT_MANIFEST.sha256"

cp -a "$TOOLS/Dockerfile.scratch" "$CTX/Dockerfile"
docker build --platform linux/amd64 -t "$STAGING_TAG" "$CTX"

mkdir -p "$EXTRACT"
CID="$(docker create --platform linux/amd64 "$STAGING_TAG")"
docker cp "$CID:/ott-supplement/." "$EXTRACT/"
docker rm "$CID" >/dev/null
python3 "$TOOLS/verify_extracted.py" "$EXTRACT" "$CONTENT_ROOT"
echo "PASS" > "$RECEIPTS/LOCAL_SUPPLEMENT_BYTE_IDENTITY.txt"

# --- local GateSimulator smoke: extracted bin + libgate from base runtime ---
mkdir -p "$SMOKE_LIB"
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
  -e OTT_SMOKE_OUT=LOCAL_GATESIMULATOR_SMOKE.json \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$SMOKE_LIB:/tmp/ott-d6502-smoke/lib:ro" \
  -v "$TOOLS:/ott/gha/tools/ott_v056_d6502_freeze:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_d6502_freeze/inimage_smoke.py
SMOKE_RC=$?
set -e
if [ "$SMOKE_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_REGENERATION_MISMATCH
fi
echo "PASS" > "$RECEIPTS/LOCAL_GATESIMULATOR_SMOKE.txt"
python3 - <<PY
import json
from pathlib import Path
p = Path("$RECEIPTS/LOCAL_GATESIMULATOR_SMOKE.json")
smoke = json.loads(p.read_text()) if p.exists() else {}
doc = {
  "LOCAL_SUPPLEMENT_BYTE_IDENTITY": "PASS",
  "LOCAL_GATESIMULATOR_SMOKE": "PASS",
  "content_root": "$CONTENT_ROOT",
  "staging_tag": "$STAGING_TAG",
  "smoke": smoke,
}
Path("$RECEIPTS/LOCAL_VERIFICATION.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
PY

IMAGE_ID="$(docker inspect --format '{{.Id}}' "$STAGING_TAG")"
echo "$IMAGE_ID" > "$RECEIPTS/SUPPLEMENT_IMAGE_ID.txt"

# Drop the 272 MB payload from the GHA workspace before push receipts copy.
rm -f "$OUT/Decoder6502.bin" "$CTX/Decoder6502.bin" "$SMOKE_LIB/Decoder6502.bin"
# Keep EXTRACT bin only long enough? Already verified; delete before upload.
rm -f "$EXTRACT/Decoder6502.bin"

# --- push with repository GITHUB_TOKEN only ---
if [ -z "${GITHUB_TOKEN:-}" ]; then
  stop STOP_D6502_SUPPLEMENT_GHCR_PUSH_UNAVAILABLE
fi
set +e
printf '%s' "$GITHUB_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
PUSH_LOGIN_RC=$?
set -e
if [ "$PUSH_LOGIN_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_GHCR_PUSH_UNAVAILABLE
fi
set +e
PUSH_OUT="$(docker push "$STAGING_TAG" 2>&1)"
PUSH_RC=$?
set -e
printf '%s\n' "$PUSH_OUT" | tee "$RECEIPTS/DOCKER_PUSH.txt" >/dev/null
printf '%s\n' "$PUSH_OUT"
if [ "$PUSH_RC" -ne 0 ]; then
  stop STOP_D6502_SUPPLEMENT_GHCR_PUSH_UNAVAILABLE
fi

DIGEST_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$STAGING_TAG" 2>/dev/null || true)"
DIGEST="${DIGEST_REF##*@}"
if [ -z "$DIGEST" ] || [ "$DIGEST" = "$DIGEST_REF" ]; then
  DIGEST="$(printf '%s\n' "$PUSH_OUT" | awk '/digest: sha256:/{for(i=1;i<=NF;i++) if($i ~ /^sha256:/) {print $i; exit}}')"
fi
if [ -z "$DIGEST" ] || [ "$DIGEST" = "$DIGEST_REF" ]; then
  DIGEST="$(docker buildx imagetools inspect "$STAGING_TAG" 2>/dev/null | awk '/Digest:/{print $2; exit}')"
fi
case "$DIGEST" in
  sha256:*) ;;
  *) stop STOP_D6502_SUPPLEMENT_GHCR_PUSH_UNAVAILABLE ;;
esac
OCI_REF="${SUPPLEMENT_REPO}@${DIGEST}"
echo "$DIGEST" | tee "$RECEIPTS/SUPPLEMENT_OCI_DIGEST.txt"
echo "$OCI_REF" | tee "$RECEIPTS/SUPPLEMENT_OCI_REF.txt"
echo "$IMAGE_ID" > "$RECEIPTS/SUPPLEMENT_CONFIG_ID.txt"
{
  echo "staging_tag=$STAGING_TAG"
  echo "manifest_digest=$DIGEST"
  echo "oci_ref=$OCI_REF"
  echo "image_id=$IMAGE_ID"
} > "$RECEIPTS/SUPPLEMENT_OCI.json"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "oci_digest=$DIGEST"
    echo "oci_ref=$OCI_REF"
    echo "content_root=$CONTENT_ROOT"
    echo "freeze_id=$FREEZE_ID"
    echo "image_id=$IMAGE_ID"
  } >> "$GITHUB_OUTPUT"
fi

# Copy small receipts into evidence. Never copy *.bin.
shopt -s nullglob
for f in "$RECEIPTS"/*.json "$RECEIPTS"/*.md "$RECEIPTS"/*.txt "$RECEIPTS"/*.sha256; do
  cp -a "$f" "$EVIDENCE/$(basename "$f")"
done
find "$EVIDENCE" "$RECEIPTS" "$CTX" "$OUT" "$EXTRACT" "$SMOKE_LIB" -type f \( -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to leave ott-run behind" >&2
  exit 1
fi
echo "FREEZE_PUSH_COMPLETE digest=$DIGEST"
exit 0
