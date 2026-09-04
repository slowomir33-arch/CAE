#!/usr/bin/env bash
# OTT v0.5.6 Stage A — GitHub Actions host entrypoint.
# Infrastructure only. Does not alter PUBLIC_PROTOCOL_ROOT.
# Science runs inside the immutable runtime image after exclusive START.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

RUN_ID="${OTT_RUN_ID:?OTT_RUN_ID must be injected by workflow identity step}"
PARENT_RUN_ID="${PARENT_RUN_ID:-OTT-v0.5.6-SCA-20260904T061758Z-AF83E092}"
PRIOR_PRESTART_STOP_RUN_ID="${PRIOR_PRESTART_STOP_RUN_ID:-OTT-v0.5.6-SCA-20260904T061127Z-40797FC6}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
EXECUTOR="$ROOT/tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py"
AUTH_SRC="$ROOT/evidence/v056-sca-gha/RUN_AUTHORIZATION.json"

RECEIPTS="$ROOT/gha-receipts"
RUN_DIR="$ROOT/ott-run"
ZIP_DIR="$ROOT/ott-evidence-zip"
PROTOCOL_DIR="$RECEIPTS/public_protocol"
mkdir -p "$RECEIPTS" "$ZIP_DIR"

export PYTHONUNBUFFERED=1

status() { printf '%s\n' "$*" | tee -a "$RECEIPTS/entrypoint.log"; }
fail_before_start() {
  local code="$1"
  shift
  status "PRESTART_STOP $code $*"
  python3 "$EXECUTOR" --phase host-package \
    --receipts-dir "$RECEIPTS" --run-dir "$RUN_DIR" --zip-dir "$ZIP_DIR" \
    --run-id "$RUN_ID" --start-present no --consumed no --verdict "$code" || true
  echo "$code" > "$RECEIPTS/VERDICT.txt"
  echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
  echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
  exit 1
}

# --- runner arch ---
{
  echo "runner.name=${RUNNER_NAME:-}"
  echo "runner.os=${RUNNER_OS:-}"
  echo "runner.arch=${RUNNER_ARCH:-}"
  echo "ImageOS=${ImageOS:-}"
  echo "ImageVersion=${ImageVersion:-}"
  echo "github.sha=${GITHUB_SHA:-}"
  echo "github.run_id=${GITHUB_RUN_ID:-}"
  echo "github.run_attempt=${GITHUB_RUN_ATTEMPT:-}"
  echo "github.job=${GITHUB_JOB:-}"
  echo "github.workflow=${GITHUB_WORKFLOW:-}"
  echo "github.workflow_ref=${GITHUB_WORKFLOW_REF:-}"
  echo "github.ref=${GITHUB_REF:-}"
  echo "github.repository=${GITHUB_REPOSITORY:-}"
  echo "PARENT_RUN_ID=$PARENT_RUN_ID"
  echo "PRIOR_PRESTART_STOP_RUN_ID=$PRIOR_PRESTART_STOP_RUN_ID"
  echo "RUN_ID=$RUN_ID"
  docker --version || true
} > "$RECEIPTS/RUNNER_IDENTITY.txt"
{
  echo "GITHUB_WORKFLOW=${GITHUB_WORKFLOW:-}"
  echo "GITHUB_WORKFLOW_REF=${GITHUB_WORKFLOW_REF:-}"
  echo "GITHUB_SHA=${GITHUB_SHA:-}"
  echo "GITHUB_REF=${GITHUB_REF:-}"
  echo "GITHUB_RUN_ID=${GITHUB_RUN_ID:-}"
  echo "GITHUB_RUN_ATTEMPT=${GITHUB_RUN_ATTEMPT:-}"
} > "$RECEIPTS/WORKFLOW_PROVENANCE.txt"
echo "$PARENT_RUN_ID" > "$RECEIPTS/PARENT_RUN_ID.txt"
echo "$PRIOR_PRESTART_STOP_RUN_ID" > "$RECEIPTS/PRIOR_PRESTART_STOP_RUN_ID.txt"
echo "$RUN_ID" > "$RECEIPTS/RUN_ID.txt"

if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  fail_before_start STOP_STAGE_A_RUNNER_ARCH_MISMATCH "os=${RUNNER_OS:-} arch=${RUNNER_ARCH:-}"
fi

# --- wrapper hash (host) ---
WRAPPER_SHA256="$(sha256sum "$EXECUTOR" | awk '{print $1}')"
echo "$WRAPPER_SHA256" > "$RECEIPTS/WRAPPER_SHA256.txt"
cp -a "$EXECUTOR" "$RECEIPTS/stage_a_executor_v0.5.6.py"
cp -a "$ROOT/tools/ott_v056_stage_a/gha_entrypoint.sh" "$RECEIPTS/gha_entrypoint.sh"
sha256sum "$ROOT/tools/ott_v056_stage_a/gha_entrypoint.sh" | awk '{print $1}' > "$RECEIPTS/GHA_ENTRYPOINT_SHA256.txt"
if [ -f "$ROOT/.github/workflows/ci.yml" ]; then
  sha256sum "$ROOT/.github/workflows/ci.yml" | awk '{print $1}' > "$RECEIPTS/CI_WORKFLOW_SHA256.txt"
fi
if [ -f "$ROOT/.github/workflows/ott-v056-stage-a.yml" ]; then
  sha256sum "$ROOT/.github/workflows/ott-v056-stage-a.yml" | awk '{print $1}' > "$RECEIPTS/DEDICATED_WORKFLOW_SHA256.txt"
fi
if [ -n "${GITHUB_WORKFLOW_REF:-}" ]; then
  printf '%s\n' "$GITHUB_WORKFLOW_REF" > "$RECEIPTS/GITHUB_WORKFLOW_REF.txt"
fi

# --- public protocol + RUN_AUTHORIZATION (host, unauthenticated) ---
status "HOST_PUBLIC_PROTOCOL begin"
if ! python3 "$EXECUTOR" --phase host-public-protocol \
    --receipts-dir "$RECEIPTS" --protocol-dir "$PROTOCOL_DIR" \
    --auth-path "$AUTH_SRC" --run-id "$RUN_ID"; then
  fail_before_start STOP_STAGE_A_PUBLIC_PROTOCOL_IDENTITY_FAILURE "host public-protocol/auth gate"
fi
status "HOST_PUBLIC_PROTOCOL pass"

# --- GHCR login + digest pull ---
AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_AUTH_MODE.txt"
status "GHCR_AUTH_MODE=$AUTH_MODE"

if [ -z "${PULL_TOKEN:-}" ]; then
  fail_before_start STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE "no GHCR pull token available"
fi

set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
# Do not retain the token in the environment after login.
if [ -n "${GHCR_PULL_TOKEN+x}" ]; then
  export GHCR_PULL_TOKEN=""
fi

if [ "$LOGIN_RC" -ne 0 ]; then
  fail_before_start STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE "docker login ghcr.io failed (token not printed)"
fi

status "DOCKER_PULL $RUNTIME_REF"
set +e
docker pull "$RUNTIME_REF"
PULL_RC=$?
set -e
if [ "$PULL_RC" -ne 0 ]; then
  fail_before_start STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE "docker pull by digest failed"
fi

PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF" 2>/dev/null || true)"
PULLED_DIGEST="${PULLED_REF##*@}"
{
  echo "required=$RUNTIME_DIGEST"
  echo "pulled_ref=$PULLED_REF"
  echo "pulled_digest=$PULLED_DIGEST"
} > "$RECEIPTS/DOCKER_PULL.txt"

if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  fail_before_start STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE "RepoDigest mismatch pulled=$PULLED_DIGEST"
fi
status "PULLED_DIGEST=$PULLED_DIGEST"

# Host pytest wheels for the in-image public suite (does not mutate the image).
python3 -m pip install --target "$RECEIPTS/pytest-deps" pytest --disable-pip-version-check --no-compile -q

# --- PRESTART inside immutable image ---
# Do not mount the GHA checkout at /workspace (image CAE lives there).
# Do not create ott-run yet (D17).
status "CONTAINER_PRESTART begin"
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e OTT_RUN_ID="$RUN_ID" \
  -e PARENT_RUN_ID="$PARENT_RUN_ID" \
  -e PRIOR_PRESTART_STOP_RUN_ID="$PRIOR_PRESTART_STOP_RUN_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_WRAPPER_SHA256="$WRAPPER_SHA256" \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$PROTOCOL_DIR:/ott/protocol:ro" \
  -v "$ROOT/tools/ott_v056_stage_a:/ott/gha/tools/ott_v056_stage_a:ro" \
  -v "$AUTH_SRC:/ott/auth/RUN_AUTHORIZATION.json:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py \
    --phase prestart \
    --receipts-dir /ott/receipts \
    --protocol-dir /ott/protocol \
    --auth-path /ott/auth/RUN_AUTHORIZATION.json \
    --run-id "$RUN_ID" \
    --wrapper-path /ott/gha/tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py
PRE_RC=$?
set -e

if [ "$PRE_RC" -ne 0 ]; then
  CODE="STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE"
  if [ -f "$RECEIPTS/PRESTART_STOP_CODE.txt" ]; then
    CODE="$(tr -d '\n' < "$RECEIPTS/PRESTART_STOP_CODE.txt")"
  fi
  fail_before_start "$CODE" "container prestart exit=$PRE_RC"
fi
status "CONTAINER_PRESTART pass"

# --- exclusive START (authorization consumption) ---
if [ -e "$RUN_DIR" ]; then
  fail_before_start STOP_STAGE_A_OUTPUT_PATH_NOT_CLEAN "run dir already exists before START"
fi

status "HOST_START exclusive create"
if ! python3 "$EXECUTOR" --phase host-start \
    --receipts-dir "$RECEIPTS" --run-dir "$RUN_DIR" \
    --auth-path "$AUTH_SRC" --run-id "$RUN_ID" \
    --wrapper-path "$EXECUTOR"; then
  # START may or may not have been created; host-start records which.
  if [ -f "$RUN_DIR/START_STAGE_A.json" ]; then
    echo "YES" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
    echo "PRESENT" > "$RECEIPTS/START_STAGE_A.txt"
    python3 "$EXECUTOR" --phase host-package \
      --receipts-dir "$RECEIPTS" --run-dir "$RUN_DIR" --zip-dir "$ZIP_DIR" \
      --run-id "$RUN_ID" --start-present yes --consumed yes \
      --verdict STOP_STAGE_A_OUTPUT_WRITE_FAILURE || true
    exit 1
  fi
  fail_before_start STOP_STAGE_A_OUTPUT_WRITE_FAILURE "exclusive START failed before consumption"
fi
echo "YES" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "PRESENT" > "$RECEIPTS/START_STAGE_A.txt"
status "START_STAGE_A created — authorization consumed"

# --- science inside immutable image ---
status "CONTAINER_SCIENCE begin"
set +e
docker run --rm \
  --network none \
  -e PYTHONUNBUFFERED=1 \
  -e OTT_RUN_ID="$RUN_ID" \
  -e PARENT_RUN_ID="$PARENT_RUN_ID" \
  -e PRIOR_PRESTART_STOP_RUN_ID="$PRIOR_PRESTART_STOP_RUN_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_WRAPPER_SHA256="$WRAPPER_SHA256" \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$PROTOCOL_DIR:/ott/protocol:ro" \
  -v "$RUN_DIR:/ott/run" \
  -v "$ROOT/tools/ott_v056_stage_a:/ott/gha/tools/ott_v056_stage_a:ro" \
  -v "$AUTH_SRC:/ott/auth/RUN_AUTHORIZATION.json:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py \
    --phase science \
    --receipts-dir /ott/receipts \
    --protocol-dir /ott/protocol \
    --run-dir /ott/run \
    --auth-path /ott/auth/RUN_AUTHORIZATION.json \
    --run-id "$RUN_ID" \
    --wrapper-path /ott/gha/tools/ott_v056_stage_a/stage_a_executor_v0.5.6.py
SCI_RC=$?
set -e
echo "$SCI_RC" > "$RECEIPTS/SCIENCE_EXIT_CODE.txt"

VERDICT="STOP_STAGE_A_CAE_INFRASTRUCTURE_FAILURE"
if [ -f "$RECEIPTS/FINAL_VERDICT.txt" ]; then
  VERDICT="$(tr -d '\n' < "$RECEIPTS/FINAL_VERDICT.txt")"
elif [ -f "$RUN_DIR/FINAL_VERDICT.txt" ]; then
  VERDICT="$(tr -d '\n' < "$RUN_DIR/FINAL_VERDICT.txt")"
elif [ "$SCI_RC" -eq 0 ]; then
  VERDICT="V0.5.6_STAGE_A_RAW_EXECUTION = PASS"
fi
echo "$VERDICT" > "$RECEIPTS/VERDICT.txt"

python3 "$EXECUTOR" --phase host-package \
  --receipts-dir "$RECEIPTS" --run-dir "$RUN_DIR" --zip-dir "$ZIP_DIR" \
  --run-id "$RUN_ID" --start-present yes --consumed yes --verdict "$VERDICT" || true

if [ "$SCI_RC" -ne 0 ]; then
  status "SCIENCE_STOP $VERDICT exit=$SCI_RC"
  exit 1
fi
status "SCIENCE_PASS $VERDICT"
exit 0
