#!/usr/bin/env bash
# libisa6502 PRESTART diagnostic host entrypoint.
# Does NOT create START_STAGE_A.json and does NOT consume RUN_AUTHORIZATION.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

DIAG_ID="${OTT_DIAGNOSTIC_ID:?OTT_DIAGNOSTIC_ID must be injected by workflow identity step}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
SUPPLEMENT_REF="${OTT_SUPPLEMENT_REF:-ghcr.io/slowomir33-arch/cae-ott-v056-d6502-supplement@sha256:b5f0938a6706f33add9e624072c1a6cab542a2fbf5eea899880778243a74ee20}"
SUPPLEMENT_DIGEST="${OTT_SUPPLEMENT_DIGEST:-sha256:b5f0938a6706f33add9e624072c1a6cab542a2fbf5eea899880778243a74ee20}"
SUPPLEMENT_CONTENT_ROOT="${OTT_SUPPLEMENT_CONTENT_ROOT:-5bd5679a5ca297eb1d2b2a84d1b68c900b54d98ea7cd0c5ac672ec903e5a48ea}"

RECEIPTS="$ROOT/gha-isa6502-receipts"
EVIDENCE="$ROOT/evidence/v056-libisa6502-diagnostic"
SUPPLEMENT_EXTRACT="$ROOT/ott-d6502-supplement-extract"
mkdir -p "$RECEIPTS" "$EVIDENCE"

echo "$DIAG_ID" > "$RECEIPTS/DIAGNOSTIC_ID.txt"
echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
echo "NO" > "$RECEIPTS/STAGE_A_EXECUTION.txt"
echo "0" > "$RECEIPTS/SCIENTIFIC_OBSERVATIONS.txt"
{
  echo "GITHUB_WORKFLOW=${GITHUB_WORKFLOW:-}"
  echo "GITHUB_WORKFLOW_REF=${GITHUB_WORKFLOW_REF:-}"
  echo "GITHUB_SHA=${GITHUB_SHA:-}"
  echo "GITHUB_REF=${GITHUB_REF:-}"
  echo "GITHUB_RUN_ID=${GITHUB_RUN_ID:-}"
  echo "GITHUB_RUN_ATTEMPT=${GITHUB_RUN_ATTEMPT:-}"
  echo "PARENT_STAGE_A_RUN_ID=OTT-v0.5.6-SCA-20260904T124104Z-9A3DE0B9"
  echo "GITHUB_PARENT_RUN_ID=33874006921"
  echo "GENERATION_2_RUN_AUTHORIZATION_SHA256=cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26"
  echo "DIAGNOSTIC_ID=$DIAG_ID"
} > "$RECEIPTS/WORKFLOW_PROVENANCE.txt"

stop() {
  local code="$1"
  echo "$code" | tee "$RECEIPTS/DIAGNOSTIC_STOP.txt" >&2
  echo "NO" > "$EVIDENCE/RUN_AUTHORIZATION_CONSUMED.txt"
  echo "ABSENT" > "$EVIDENCE/START_STAGE_A.txt"
  echo "NO" > "$EVIDENCE/STAGE_A_EXECUTION.txt"
  rm -f "${SUPPLEMENT_EXTRACT:-}/Decoder6502.bin"
  find "$EVIDENCE" "$RECEIPTS" -type f \( -name '*.so' -o -name 'Decoder6502.bin' -o -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
  exit 1
}

if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi

# Never create Stage-A run directory. Never invoke the Stage-A executor.
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to proceed: ott-run exists; Stage A path must stay unused" >&2
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi

sha256sum "$ROOT/tools/ott_v056_libisa6502/gha_entrypoint.sh" | awk '{print $1}' > "$RECEIPTS/GHA_ENTRYPOINT_SHA256.txt"
sha256sum "$ROOT/tools/ott_v056_libisa6502/libisa6502_diagnostic.py" | awk '{print $1}' > "$RECEIPTS/LIBISA6502_DIAGNOSTIC_PY_SHA256.txt"
sha256sum "$ROOT/.github/workflows/ci.yml" | awk '{print $1}' > "$RECEIPTS/CI_WORKFLOW_SHA256.txt"

AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_AUTH_MODE.txt"
if [ -z "${PULL_TOKEN:-}" ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi

set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
export GHCR_PULL_TOKEN=""
if [ "$LOGIN_RC" -ne 0 ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi

docker pull "$RUNTIME_REF"
PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF" 2>/dev/null || true)"
PULLED_DIGEST="${PULLED_REF##*@}"
echo "required=$RUNTIME_DIGEST pulled=$PULLED_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_BASE.txt"
if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
docker logout ghcr.io >/dev/null 2>&1 || true

# Frozen Decoder6502 supplement by digest only. Do not generate Decoder6502.bin.
if [ -z "${GITHUB_TOKEN:-}" ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
set +e
printf '%s' "$GITHUB_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
SUP_LOGIN_RC=$?
set -e
if [ "$SUP_LOGIN_RC" -ne 0 ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
set +e
docker pull "$SUPPLEMENT_REF"
SUP_PULL_RC=$?
set -e
if [ "$SUP_PULL_RC" -ne 0 ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
GOT_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$SUPPLEMENT_REF" 2>/dev/null || true)"
GOT_DIGEST="${GOT_REF##*@}"
echo "required=$SUPPLEMENT_DIGEST pulled=$GOT_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_SUPPLEMENT.txt"
if [ "$GOT_DIGEST" != "$SUPPLEMENT_DIGEST" ]; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
mkdir -p "$SUPPLEMENT_EXTRACT"
SUP_CID="$(docker create --platform linux/amd64 "$SUPPLEMENT_REF" /bin/true)"
docker cp "$SUP_CID:/ott-supplement/." "$SUPPLEMENT_EXTRACT/"
docker rm "$SUP_CID" >/dev/null
if ! python3 "$ROOT/tools/ott_v056_d6502_freeze/verify_extracted.py" "$SUPPLEMENT_EXTRACT" "$SUPPLEMENT_CONTENT_ROOT"; then
  stop STOP_LIBISA6502_PARENT_IDENTITY_FAILURE
fi
docker logout ghcr.io >/dev/null 2>&1 || true

# Do not mount the GHA checkout at /workspace (image CAE lives there).
# Do not mount ott-run. Do not invoke the Stage-A execution wrapper.
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e OTT_DIAGNOSTIC_ID="$DIAG_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_RECEIPTS_DIR=/ott/receipts \
  -e OTT_SUPPLEMENT_DIR=/ott-supplement \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$ROOT/tools/ott_v056_libisa6502:/ott/gha/tools/ott_v056_libisa6502:ro" \
  -v "$SUPPLEMENT_EXTRACT:/ott-supplement:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_libisa6502/libisa6502_diagnostic.py
RC=$?
set -e

# Copy small receipts into the evidence path. Never copy *.so / *.bin tables.
shopt -s nullglob
for f in "$RECEIPTS"/*.json "$RECEIPTS"/*.md "$RECEIPTS"/*.txt; do
  base="$(basename "$f")"
  case "$base" in
    *.bin|*.so) continue ;;
  esac
  cp -a "$f" "$EVIDENCE/$base"
done

echo "NO" > "$EVIDENCE/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$EVIDENCE/START_STAGE_A.txt"
echo "NO" > "$EVIDENCE/STAGE_A_EXECUTION.txt"
echo "0" > "$EVIDENCE/SCIENTIFIC_OBSERVATIONS.txt"

rm -f "$SUPPLEMENT_EXTRACT/Decoder6502.bin"
find "$EVIDENCE" "$RECEIPTS" "$SUPPLEMENT_EXTRACT" -type f \( -name '*.so' -o -name 'Decoder6502.bin' -o -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to leave ott-run behind; Stage A path must stay unused" >&2
  rm -rf "$ROOT/ott-run"
  exit 1
fi

if [ ! -f "$EVIDENCE/LIBISA6502_CLASSIFICATION.json" ]; then
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$EVIDENCE/LIBISA6502_CLASSIFICATION.txt"
fi

exit "$RC"
