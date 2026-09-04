# OTT v0.5.6 — SCIENTIFIC STAGE A RAW EXECUTION REPORT

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: SCIENTIFIC_STAGE_A_RAW_EXECUTION
RUN_ID: OTT-v0.5.6-SCA-20260904T061758Z-AF83E092
MESSAGE_ID: OTT-v0.5.6-SCA-20260904T061758Z-AF83E092-M001
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T06:29:40Z
AGENT: Cursor Agent Cursor Grok 4.6
PARENT_P2B_RUN_ID: OTT-v0.5.6-P2B-20260904T055902Z-1D12E2EF
PARENT_P2B_COMMIT: 27f157d6767e77bdb9a07d63e742aec28e100793
PUBLIC_V0_5_6_DOI: 10.5281/zenodo.22293061
PUBLIC_PROTOCOL_ZIP_SHA256: 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PUBLIC_PROTOCOL_ROOT_SHA256: b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
RUN_AUTHORIZATION_SHA256: 4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358
RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
END_OTT_REPORT_SIGNATURE

EXECUTION_ENVIRONMENT: GitHub Actions ubuntu-latest linux/X64 (attempted; dispatch did not start a runner)
PREVIOUS_PRESTART_STOP_RUN_ID: OTT-v0.5.6-SCA-20260904T061127Z-40797FC6

## 1. Verdict

```
STOP_STAGE_A_GHA_DISPATCH_UNAVAILABLE
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
IN_PLACE_RESUME = FORBIDDEN
```

Infrastructure for Stage A is on branch `cursor/ott-v056-sca-gha-5ef6` / PR #13.
This Cloud Agent cannot create `workflow_dispatch` events (`gh` is read-only / integration 403).
The dedicated workflow is not present on `main` (GitHub 404).
A push/PR trigger was not added.

## 2. Report identity

RUN_ID `OTT-v0.5.6-SCA-20260904T061758Z-AF83E092` (new; previous STOP id not reused).

## 3–7. Gates not executed on a GHA runner

Public ZIP, runtime digest pull, 48/48 tests, wrapper conformance, and Lilotane discovery
were not executed because no GHA job started.

Local copy of `RUN_AUTHORIZATION.json` still hashes to
`4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358`
with `consumed=false` and `start_stage_a=ABSENT`.

## 8. START_STAGE_A / authorization consumption

Not created.

## 9–18. Science / seal

Not run.

## 19. Deviations / STOPs

1. `gh workflow run ott-v056-stage-a.yml --ref cursor/ott-v056-sca-gha-5ef6` → HTTP 404
   (workflow file not on default branch).
2. `gh workflow run ci.yml --ref cursor/ott-v056-sca-gha-5ef6` → HTTP 403
   Resource not accessible by integration.
3. PR #13 opened a `pull_request` CI run for unit tests only. The Stage A job is
   `if: github.event_name == 'workflow_dispatch'` and did not start.

To proceed, an authorized actor must dispatch either:

- `.github/workflows/ott-v056-stage-a.yml` from this branch after the workflow exists on `main`, or
- workflow `CI` on ref `cursor/ott-v056-sca-gha-5ef6` (Stage A job only; tests skipped on dispatch).

Do not rerun after a later START. This authorization is still unconsumed.

## 20. Final strings

```
V0.5.6_STAGE_A_RAW_EXECUTION = NOT STARTED
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
CANDIDATE_SELECTION_COUNT = 0
HELD_OUT_COUNT = 0
EXTERNAL_LABEL_JOIN_COUNT = 0
SCORING_COUNT = 0
VERDICT_COUNT = 0
STAGE_A_READY_FOR_AUDIT = NO
STOP.
```
