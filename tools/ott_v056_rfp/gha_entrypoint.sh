#!/usr/bin/env bash
# Runtime fingerprint PRESTART diagnostic host entrypoint.
# Does NOT create START_STAGE_A.json and does NOT consume RUN_AUTHORIZATION.
# Does NOT mutate/push the base runtime or Decoder supplement.
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

DIAG_ID="${OTT_DIAGNOSTIC_ID:?OTT_DIAGNOSTIC_ID must be injected by workflow identity step}"
RUNTIME_REF="${OTT_RUNTIME_REF:-ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"
RUNTIME_DIGEST="${OTT_RUNTIME_DIGEST:-sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8}"

RECEIPTS="$ROOT/gha-rfp-receipts"
EVIDENCE="$ROOT/evidence/v056-runtime-fingerprint-diagnostic"
mkdir -p "$RECEIPTS" "$EVIDENCE"

echo "$DIAG_ID" > "$RECEIPTS/DIAGNOSTIC_ID.txt"
echo "NO" > "$RECEIPTS/RUN_AUTHORIZATION_CONSUMED.txt"
echo "ABSENT" > "$RECEIPTS/START_STAGE_A.txt"
echo "NO" > "$RECEIPTS/STAGE_A_EXECUTION.txt"
echo "0" > "$RECEIPTS/SCIENTIFIC_OBSERVATIONS.txt"
echo "0" > "$RECEIPTS/DOI_SEEDS_DERIVED.txt"
echo "0" > "$RECEIPTS/IPC_SPLIT_DERIVED.txt"
{
  echo "GITHUB_WORKFLOW=${GITHUB_WORKFLOW:-}"
  echo "GITHUB_WORKFLOW_REF=${GITHUB_WORKFLOW_REF:-}"
  echo "GITHUB_SHA=${GITHUB_SHA:-}"
  echo "GITHUB_REF=${GITHUB_REF:-}"
  echo "GITHUB_RUN_ID=${GITHUB_RUN_ID:-}"
  echo "GITHUB_RUN_ATTEMPT=${GITHUB_RUN_ATTEMPT:-}"
  echo "PARENT_STAGE_A_RUN_ID=OTT-v0.5.6-SCA-20260904T133624Z-33FAE80C"
  echo "GITHUB_PARENT_RUN_ID=33878994052"
  echo "GENERATION_2_RUN_AUTHORIZATION_SHA256=cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26"
  echo "DIAGNOSTIC_ID=$DIAG_ID"
} > "$RECEIPTS/WORKFLOW_PROVENANCE.txt"

stop() {
  local code="$1"
  echo "$code" | tee "$RECEIPTS/DIAGNOSTIC_STOP.txt" >&2
  echo "NO" > "$EVIDENCE/RUN_AUTHORIZATION_CONSUMED.txt"
  echo "ABSENT" > "$EVIDENCE/START_STAGE_A.txt"
  echo "NO" > "$EVIDENCE/STAGE_A_EXECUTION.txt"
  find "$EVIDENCE" "$RECEIPTS" -type f \( -name '*.so' -o -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
  exit 1
}

if [ "${RUNNER_OS:-}" != "Linux" ] || [ "${RUNNER_ARCH:-}" != "X64" ]; then
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi

if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to proceed: ott-run exists; Stage A path must stay unused" >&2
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi

sha256sum "$ROOT/tools/ott_v056_rfp/gha_entrypoint.sh" | awk '{print $1}' > "$RECEIPTS/GHA_ENTRYPOINT_SHA256.txt"
sha256sum "$ROOT/tools/ott_v056_rfp/rfp_diagnostic.py" | awk '{print $1}' > "$RECEIPTS/RFP_DIAGNOSTIC_PY_SHA256.txt"
sha256sum "$ROOT/.github/workflows/ci.yml" | awk '{print $1}' > "$RECEIPTS/CI_WORKFLOW_SHA256.txt"

AUTH_MODE="GITHUB_TOKEN"
PULL_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  AUTH_MODE="GHCR_PULL_TOKEN"
  PULL_TOKEN="$GHCR_PULL_TOKEN"
fi
echo "$AUTH_MODE" > "$RECEIPTS/GHCR_AUTH_MODE.txt"
if [ -z "${PULL_TOKEN:-}" ]; then
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi

set +e
printf '%s' "$PULL_TOKEN" | docker login ghcr.io -u "${GITHUB_ACTOR:-github-actions}" --password-stdin
LOGIN_RC=$?
set -e
unset PULL_TOKEN || true
export GHCR_PULL_TOKEN=""
if [ "$LOGIN_RC" -ne 0 ]; then
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi

docker pull "$RUNTIME_REF"
PULLED_REF="$(docker inspect --format '{{index .RepoDigests 0}}' "$RUNTIME_REF" 2>/dev/null || true)"
PULLED_DIGEST="${PULLED_REF##*@}"
echo "required=$RUNTIME_DIGEST pulled=$PULLED_DIGEST" | tee "$RECEIPTS/DOCKER_PULL_BASE.txt"
if [ "$PULLED_DIGEST" != "$RUNTIME_DIGEST" ]; then
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi

docker inspect "$RUNTIME_REF" > "$RECEIPTS/IMAGE_INSPECT.json"
docker history --no-trunc "$RUNTIME_REF" > "$RECEIPTS/IMAGE_HISTORY.txt"
set +e
python3 - "$RECEIPTS" "$RUNTIME_DIGEST" "$PULLED_DIGEST" "$PULLED_REF" <<'PY'
import json, sys
from pathlib import Path
receipts = Path(sys.argv[1])
required, pulled, pulled_ref = sys.argv[2], sys.argv[3], sys.argv[4]
ins = json.loads((receipts / "IMAGE_INSPECT.json").read_text(encoding="utf-8"))
info = ins[0] if isinstance(ins, list) else ins
cfg = info.get("Config") or {}
parent = {
    "document": "PARENT_OCI_IDENTITY",
    "required_digest": required,
    "pulled_digest": pulled,
    "pulled_ref": pulled_ref,
    "id": info.get("Id"),
    "repo_digests": info.get("RepoDigests"),
    "architecture": info.get("Architecture"),
    "os": info.get("Os"),
    "variant": info.get("Variant"),
    "config_digest": (info.get("Config") or {}).get("Image"),
    "rootfs": info.get("RootFS"),
    "labels": cfg.get("Labels"),
    "platform": {
        "architecture": info.get("Architecture"),
        "os": info.get("Os"),
    },
    "PASS": pulled == required,
}
(receipts / "PARENT_OCI_IDENTITY.json").write_text(json.dumps(parent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if not parent["PASS"]:
    raise SystemExit(2)
print("PARENT_OCI_IDENTITY PASS")
PY
OCI_RC=$?
set -e
if [ "$OCI_RC" -ne 0 ]; then
  stop STOP_RFP_PARENT_OCI_IDENTITY_FAILURE
fi
docker logout ghcr.io >/dev/null 2>&1 || true

# Do not mount GHA checkout at /workspace. Do not mount ott-run.
# Do not invoke Stage-A execution wrapper. Do not pull/mutate supplement.
# Image filesystem is read-only; receipts are a host bind.
set +e
docker run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e OTT_DIAGNOSTIC_ID="$DIAG_ID" \
  -e OTT_RUNTIME_DIGEST="$RUNTIME_DIGEST" \
  -e OTT_RECEIPTS_DIR=/ott/receipts \
  -v "$RECEIPTS:/ott/receipts" \
  -v "$ROOT/tools/ott_v056_rfp:/ott/gha/tools/ott_v056_rfp:ro" \
  "$RUNTIME_REF" \
  python3 /ott/gha/tools/ott_v056_rfp/rfp_diagnostic.py
RC=$?
set -e

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
echo "0" > "$EVIDENCE/DOI_SEEDS_DERIVED.txt"
echo "0" > "$EVIDENCE/IPC_SPLIT_DERIVED.txt"

find "$EVIDENCE" "$RECEIPTS" -type f \( -name '*.so' -o -name '*.bin' -o -size +10M \) -delete 2>/dev/null || true
if [ -e "$ROOT/ott-run" ]; then
  echo "refusing to leave ott-run behind; Stage A path must stay unused" >&2
  rm -rf "$ROOT/ott-run"
  exit 1
fi

if [ ! -f "$EVIDENCE/FINGERPRINT_CLASSIFICATION.json" ]; then
  echo "C_RUNTIME_FINGERPRINT_CONTRADICTION" > "$EVIDENCE/FINGERPRINT_CLASSIFICATION.txt"
fi

exit "$RC"
