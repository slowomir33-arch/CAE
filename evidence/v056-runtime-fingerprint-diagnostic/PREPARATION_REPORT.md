# OTT v0.5.6 — RUNTIME FINGERPRINT PRESTART DIAGNOSTIC (CURSOR PREPARATION)

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: RUNTIME_FINGERPRINT_PRESTART_DIAGNOSTIC
RUN_ID: ABSENT
MESSAGE_ID: ABSENT
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T13:52:09Z
AGENT: Cursor Agent runtime-fingerprint PRESTART diagnostic preparation
PARENT_STAGE_A_RUN_ID: OTT-v0.5.6-SCA-20260904T133624Z-33FAE80C
PARENT_GITHUB_RUN_ID: 33878994052
GENERATION_2_RUN_AUTHORIZATION_SHA256: cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26
BASE_RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
END_OTT_REPORT_SIGNATURE

Preparation only. Diagnostic RUN_ID is generated on the GitHub Actions runner
as `OTT-v0.5.6-RFP-<YYYYMMDDTHHMMSSZ>-<8HEX>`. This integration cannot
dispatch. Classification A/B/C is therefore not declared here.

Packet SHA-256 matched:

```
8616ead1cadc405976f5d4d2672f498fa2fb33eb8300a7f84d96f31b962980fe
```

Parent Stage-A failure under diagnosis:

```
STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE: fingerprint root not found in image
HEAD 15244162fc6c21fa191438ff525fda266b5e637f
```

GHA job `ott-v056-runtime-fingerprint-diagnostic` is the sole
`workflow_dispatch` execution job. Stage A, libisa6502 diagnostic,
Decoder6502 diagnostic, freeze, and retrieve remain `if: false`.

The diagnostic pulls the frozen OCI runtime by digest only, runs the image
read-only with `--network none`, does not mount the GHA checkout at
`/workspace`, and does not invoke the Stage-A executor.

```
STOP_RFP_GHA_DISPATCH_UNAVAILABLE

STATIC_VALIDATION = PASS
STAGE_A_JOB = DISABLED
RFP_DIAGNOSTIC_JOB = workflow_dispatch only
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
STAGE_A_EXECUTION = NO
DOI_SEEDS_DERIVED = 0
IPC_SPLIT_DERIVED = 0

GENERATION_2_RUN_AUTHORIZATION_SHA256 =
cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26

GENERATION_2_RUN_AUTHORIZATION_STATUS = UNCONSUMED

RUNTIME_FINGERPRINT_CLASSIFICATION = NOT_DECLARED_IN_PREPARATION

READY_FOR_AUDITOR_REVIEW = YES
```

Exact author dispatch (registered `CI` workflow, this branch):

```
gh workflow run ci.yml --ref cursor/ott-v056-sca-gha-5ef6
```

Do not merge PR #13.
STOP.
