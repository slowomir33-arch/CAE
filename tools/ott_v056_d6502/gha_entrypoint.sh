#!/usr/bin/env bash
# Decoder6502 PRESTART diagnostic host entrypoint.
# Does NOT create START_STAGE_A.json and does NOT consume RUN_AUTHORIZATION.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

DIAG_ID="${OTT_DIAGNOSTIC_ID:?OTT_DIAGNOSTIC_ID must be injected by workflow identity step}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"

RECEIPTS="$ROOT/gha-d6502-receipts"
EVIDENCE="$ROOT/evidence/v056-d6502-diagnostic"
mkdir -p "$RECEIPTS" "$EVIDENCE"

echo "$DIAG_ID" > "$RECEIPTS/DIAGNOSTIC_ID.txt"
echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
echo "NO" > "$RECEIPTS/STAGE_A_EXECUTION.txt"
{
  echo "GITHUB_WORKFLOW=${GITHUB_WORKFLOW:-}"
  echo "GITHUB_WORKFLOW_REF=${GITHUB_WORKFLOW_REF:-}"
  echo "GITHUB_SHA=${GITHUB_SHA:-}"
  echo "GITHUB_REF=${GITHUB_REF:-}"
  echo "GITHUB_RUN_ID=${GITHUB_RUN_ID:-}"
  echo "GITHUB_RUN_ATTEMPT=${GITHUB_RUN_ATTEMPT:-}"
  echo "PARENT_STAGE_A_RUN_ID=OTT-v0.5.6-SCA-20260904T105201Z-BC6F6E8E"
  echo "GITHUB_PARENT_RUN_ID=33865237389"
  echo "DIAGNOSTIC_ID=$DIAG_ID"
} > "$RECEIPTS/WORKFLOW_PROVENANCE.txt"

if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  echo "STOP_D6502_RUNTIME_IDENTITY_FAILURE runner os=${RUNNER_OS:-} arch=${RUNNER_ARCH:-}" >&2
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$RECEIPTS/D6502_CLASSIFICATION.txt"
  exit 1
fi

# Never create Stage-A run directory. Never invoke the Stage-A executor.
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to proceed: ott-run exists; Stage A path must stay unused" >&2
  exit 1
fi
sha256sum "$ROOT/tools/ott_v056_d6502/gha_entrypoint.sh" | awk '{print $1}' > "$RECEIPTS/GHA_ENTRYPOINT_SHA256.txt"
sha256sum "$ROOT/tools/ott_v056_d6502/d6502_diagnostic.py" | awk '{print $1}' > "$RECEIPTS/D6502_DIAGNOSTIC_PY_SHA256.txt"
sha256sum "$ROOT/.github/workflows/ci.yml" | awk '{print $1}' > "$RECEIPTS/CI_WORKFLOW_SHA256.txt"

AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_AUTH_MODE.txt"

if [ -z "${PULL_TOKEN:-}" ]; then
  echo "STOP_D6502_RUNTIME_IDENTITY_FAILURE no pull token" >&2
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$RECEIPTS/D6502_CLASSIFICATION.txt"
  exit 1
fi

set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
export GHCR_PULL_TOKEN=""

if [ "$LOGIN_RC" -ne 0 ]; then
  echo "STOP_D6502_RUNTIME_IDENTITY_FAILURE docker login failed" >&2
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$RECEIPTS/D6502_CLASSIFICATION.txt"
  exit 1
fi

docker pull "$RUNTIME_REF"
PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF")"
PULLED_DIGEST="${PULLED_REF##*@}"
echo "PULLED_DIGEST=$PULLED_DIGEST" | tee "$RECEIPTS/DOCKER_PULL.txt"
if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  echo "STOP_D6502_RUNTIME_IDENTITY_FAILURE digest mismatch" >&2
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$RECEIPTS/D6502_CLASSIFICATION.txt"
  exit 1
fi

# Do not mount checkout at /workspace. Do not mount ott-run.
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e OTT_DIAGNOSTIC_ID="$DIAG_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_RECEIPTS_DIR=/ott/receipts \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$ROOT/tools/ott_v056_d6502:/ott/gha/tools/ott_v056_d6502:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_d6502/d6502_diagnostic.py
RC=$?
set -e

# Copy small receipts into the evidence path. Never copy *.bin tables.
shopt -s nullglob
for f in "$RECEIPTS"/*.json "$RECEIPTS"/*.md "$RECEIPTS"/*.txt; do
  base="$(basename "$f")"
  case "$base" in
    *.bin) continue ;;
  esac
  cp -a "$f" "$EVIDENCE/$base"
done

echo "NO" > "$EVIDENCE/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$EVIDENCE/START_STAGE_A.txt"
echo "NO" > "$EVIDENCE/STAGE_A_EXECUTION.txt"

# Guarantee no 272 MB table leaked into workspace evidence.
find "$EVIDENCE" "$RECEIPTS" -type f \( -name 'Decoder6502.bin' -o -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to leave ott-run behind; Stage A path must stay unused" >&2
  rm -rf "$ROOT/ott-run"
  exit 1
fi

if [ ! -f "$EVIDENCE/D6502_CLASSIFICATION.json" ]; then
  echo "C_RUNTIME_SUPERSESSION_REQUIRED" > "$EVIDENCE/D6502_CLASSIFICATION.txt"
fi

exit "$RC"
