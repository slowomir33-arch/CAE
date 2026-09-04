# OTT v0.5.6 — RUNTIME FINGERPRINT EXTERNAL BINDING PREPARATION

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: RUNTIME_FINGERPRINT_EXTERNAL_BINDING_PREPARATION
RUN_ID: OTT-v0.5.6-RFPB-20260904T140712Z-B0051B10
MESSAGE_ID: OTT-v0.5.6-RFPB-20260904T140712Z-B0051B10-M001
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T14:07:12Z
AGENT: Cursor Agent runtime-fingerprint false-positive correction and external binding
PARENT_RFP_RUN_ID: OTT-v0.5.6-RFP-20260904T135535Z-EC702FE2
PARENT_GITHUB_RUN_ID: 33880765807
GENERATION_2_RUN_AUTHORIZATION_SHA256: cb194c51d80937842a816544a3f377673f18e9206e48003c0c636711282f9e26
END_OTT_REPORT_SIGNATURE

Packet SHA-256 matched:

```
8c4cb0cc3f49f79158055faf982ca2dff8b7125f1e8c7c0e2ec6839c1ee31768
```

Auditor rejected runner class C as a diagnostic false positive. The only
alleged contradiction was `/opt/ott/source_closure_prefreeze.json` containing
the known Solver.h patch SHA
`ef46037f57eef6b84b0a2bdca42543f9961b627c420aabc8ba4d055ded6f1b52`.
That is not a competing runtime fingerprint authority.

Immutable-image search found 0 accepted fingerprint-root hits and 0 accepted
fingerprint JSON SHA hits (`files_seen = 83653`, `read_errors = 0`).

Stage-A PRESTART no longer requires a fingerprint file inside the OCI
filesystem. Identity is the exact cross-binding of generation-2
`RUN_AUTHORIZATION` bytes, accepted fingerprint root, authorization base
runtime digest, and actual pulled OCI digest. No generation-3 authorization.
No fingerprint file was synthesized. No runtime rebuild. No dispatch.

```
RFP_FALSE_POSITIVE_CORRECTION = PASS

RUNNER_CLASS_C_STATUS =
REJECTED_FALSE_POSITIVE

AUDITOR_RFP_CLASSIFICATION =
B_FINGERPRINT_NOT_EMBEDDED_AUDITOR_DECISION_REQUIRED

RUNTIME_FINGERPRINT_EXTERNAL_BINDING =
PREPARED

GENERATION_2_RUN_AUTHORIZATION_STATUS =
UNCONSUMED

NEW_AUTHORIZATION_REQUIRED = NO

RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
STAGE_A_EXECUTION = NO

STAGE_A_GHA_STATIC_PREPARATION = PASS
WORKFLOW_DISPATCH = NOT PERFORMED

READY_FOR_AUDITOR_REVIEW = YES
```

Exact author dispatch (registered `CI` workflow, this branch; not performed):

```
gh workflow run ci.yml --ref cursor/ott-v056-sca-gha-5ef6
```

Do not merge PR #13.
STOP.
