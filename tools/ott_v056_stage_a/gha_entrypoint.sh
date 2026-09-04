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
AUTH_SRC="$ROOT/evidence/v056-stage-a-reauthorization/RUN_AUTHORIZATION.json"
SUPPLEMENT_REF="${OTT_SUPPLEMENT_REF:-ghcr.io/slowomir33-arch/cae-ott-v056-d6502-supplement@sha256:b5f0938a6706f33add9e624072c1a6cab542a2fbf5eea899880778243a74ee20}"
SUPPLEMENT_DIGEST="${OTT_SUPPLEMENT_DIGEST:-sha256:b5f0938a6706f33add9e624072c1a6cab542a2fbf5eea899880778243a74ee20}"
SUPPLEMENT_CONTENT_ROOT="${OTT_SUPPLEMENT_CONTENT_ROOT:-5bd5679a5ca297eb1d2b2a84d1b68c900b54d98ea7cd0c5ac672ec903e5a48ea}"
CPU_LIB="$ROOT/ott-cpu6502-lib"
SUPPLEMENT_EXTRACT="$ROOT/ott-d6502-supplement-extract"

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
  rm -f "${CPU_LIB:-}/Decoder6502.bin" "${SUPPLEMENT_EXTRACT:-}/Decoder6502.bin"
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
printf '%s\n' "$PULLED_DIGEST" > "$RECEIPTS/PULLED_RUNTIME_DIGEST.txt"
export OTT_PULLED_RUNTIME_DIGEST="$PULLED_DIGEST"

# --- bind exact Decoder6502 supplement (host, before any START) ---
# Do not generate Decoder6502.bin. Pull frozen OCI by digest only.
status "SUPPLEMENT_PULL $SUPPLEMENT_REF"
docker logout ghcr.io >/dev/null 2>&1 || true
if [ -z "${GITHUB_TOKEN:-}" ]; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "no GITHUB_TOKEN for supplement pull"
fi
set +e
printf '%s' "$GITHUB_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
SUP_LOGIN_RC=$?
set -e
if [ "$SUP_LOGIN_RC" -ne 0 ]; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "supplement docker login failed"
fi
set +e
docker pull "$SUPPLEMENT_REF"
SUP_PULL_RC=$?
set -e
if [ "$SUP_PULL_RC" -ne 0 ]; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "supplement pull by digest failed"
fi
GOT_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$SUPPLEMENT_REF" 2>/dev/null || true)"
GOT_DIGEST="${GOT_REF##*@}"
echo "required=$SUPPLEMENT_DIGEST pulled=$GOT_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_SUPPLEMENT.txt"
if [ "$GOT_DIGEST" != "$SUPPLEMENT_DIGEST" ]; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "supplement digest mismatch pulled=$GOT_DIGEST"
fi
mkdir -p "$SUPPLEMENT_EXTRACT"
rm -rf "$CPU_LIB"
mkdir -p "$CPU_LIB"
SUP_CID="$(docker create --platform linux/amd64 "$SUPPLEMENT_REF" /bin/true)"
docker cp "$SUP_CID:/ott-supplement/." "$SUPPLEMENT_EXTRACT/"
docker rm "$SUP_CID" >/dev/null
if ! python3 "$ROOT/tools/ott_v056_d6502_freeze/verify_extracted.py" "$SUPPLEMENT_EXTRACT" "$SUPPLEMENT_CONTENT_ROOT"; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "supplement extract/manifest/root mismatch"
fi
BASE_CID="$(docker create --platform linux/amd64 "$RUNTIME_REF" /bin/true)"
docker cp "$BASE_CID:/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libgate6502.so" "$CPU_LIB/libgate6502.so"
set +e
docker cp "$BASE_CID:/opt/ott/sources/CAE/systems/10_cpu_6502_libs/libisa6502.so" "$CPU_LIB/libisa6502.so"
ISA_CP_RC=$?
set -e
docker rm "$BASE_CID" >/dev/null
if [ "$ISA_CP_RC" -ne 0 ] || [ ! -f "$CPU_LIB/libisa6502.so" ]; then
  fail_before_start STOP_STAGE_A_LIBISA6502_IDENTITY_FAILURE "canonical libisa6502.so copy failed"
fi
cp -a "$SUPPLEMENT_EXTRACT/Decoder6502.bin" "$CPU_LIB/Decoder6502.bin"
set +e
CPU_LIB="$CPU_LIB" python3 - <<'PY'
import hashlib, os, sys
from pathlib import Path
lib = Path(os.environ["CPU_LIB"])
names = {p.name for p in lib.iterdir() if p.is_file()}
if names != {"Decoder6502.bin", "libgate6502.so", "libisa6502.so"}:
    sys.exit(3)
def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
dec = lib / "Decoder6502.bin"
gate = lib / "libgate6502.so"
isa = lib / "libisa6502.so"
if dec.stat().st_size != 272629760 or sha(dec) != "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62":
    sys.exit(2)
if sha(gate) != "ba8222d520c93ac8a3989857c8b2b3cb8573196ef185747eef60d8482dcf1964":
    sys.exit(5)
if isa.stat().st_size != 47576 or sha(isa) != "33df0fa6c649e7a3240a536337b00f0b8ef120eea05edeaec0910817a560f075":
    sys.exit(4)
print("CPU_SCRATCH_LIB_PASS")
PY
LIB_RC=$?
set -e
if [ "$LIB_RC" -eq 4 ] || [ "$LIB_RC" -eq 3 ]; then
  fail_before_start STOP_STAGE_A_LIBISA6502_IDENTITY_FAILURE "scratch libisa identity rc=$LIB_RC"
fi
if [ "$LIB_RC" -eq 5 ]; then
  fail_before_start STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE "scratch libgate identity"
fi
if [ "$LIB_RC" -ne 0 ]; then
  fail_before_start STOP_STAGE_A_SUPPLEMENT_IDENTITY_FAILURE "scratch lib decoder identity"
fi
status "SUPPLEMENT_BIND pass"
# Do not retain the 272 MB table in receipts/evidence.
rm -f "$SUPPLEMENT_EXTRACT/Decoder6502.bin"
docker logout ghcr.io >/dev/null 2>&1 || true

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
  -e OTT_PULLED_RUNTIME_DIGEST="${OTT_PULLED_RUNTIME_DIGEST:-$PULLED_DIGEST}" \
  -e OTT_WRAPPER_SHA256="$WRAPPER_SHA256" \
  -e CPU6502_LIB_DIR=/ott/cpu6502-lib \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$PROTOCOL_DIR:/ott/protocol:ro" \
  -v "$ROOT/tools/ott_v056_stage_a:/ott/gha/tools/ott_v056_stage_a:ro" \
  -v "$AUTH_SRC:/ott/auth/RUN_AUTHORIZATION.json:ro" \
  -v "$CPU_LIB:/ott/cpu6502-lib:ro" \
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
  -e OTT_PULLED_RUNTIME_DIGEST="${OTT_PULLED_RUNTIME_DIGEST:-$PULLED_DIGEST}" \
  -e OTT_WRAPPER_SHA256="$WRAPPER_SHA256" \
  -e CPU6502_LIB_DIR=/ott/cpu6502-lib \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$PROTOCOL_DIR:/ott/protocol:ro" \
  -v "$RUN_DIR:/ott/run" \
  -v "$ROOT/tools/ott_v056_stage_a:/ott/gha/tools/ott_v056_stage_a:ro" \
  -v "$AUTH_SRC:/ott/auth/RUN_AUTHORIZATION.json:ro" \
  -v "$CPU_LIB:/ott/cpu6502-lib:ro" \
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

rm -f "$CPU_LIB/Decoder6502.bin" "$SUPPLEMENT_EXTRACT/Decoder6502.bin"

if [ "$SCI_RC" -ne 0 ]; then
  status "SCIENCE_STOP $VERDICT exit=$SCI_RC"
  exit 1
fi
status "SCIENCE_PASS $VERDICT"
exit 0
