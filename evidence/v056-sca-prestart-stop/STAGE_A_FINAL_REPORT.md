# OTT v0.5.6 — SCIENTIFIC STAGE A RAW EXECUTION REPORT

## 1. Verdict

```
STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
READY_TO_START_STAGE_A = NO
CANDIDATE_SELECTION = NOT RUN
HELD_OUT_ABLATION = NOT RUN
EXTERNAL_LABEL_SCORING = NOT RUN
HYPOTHESIS_VERDICT = NOT RUN
```

Packet SHA-256 matched `7580707175db7154df26c6301253df4d643932d73e03f95d90dcc9377b5528df`.
PRESTART stopped before `START_STAGE_A.json`. Authorization was not consumed.

## 2. Report identity

```
RUN_ID = OTT-v0.5.6-SCA-20260904T061127Z-40797FC6
PARENT_P2B = OTT-v0.5.6-P2B-20260904T055902Z-1D12E2EF / 27f157d6767e77bdb9a07d63e742aec28e100793
PUBLIC_V0_5_6_DOI = 10.5281/zenodo.22293061
```

## 3. Public protocol verification

Unauthenticated public GET of Zenodo 22293061:

```
status = published
access = open
ZIP bytes = 58243
ZIP SHA-256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
manifest = 35 / 35
PUBLIC_PROTOCOL_ROOT_SHA256 = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
PUBLIC_PROTOCOL_BYTE_IDENTITY = PASS
```

## 4. RUN_AUTHORIZATION verification

Fetched exact P2B file at commit `27f157d6767e77bdb9a07d63e742aec28e100793`.

```
SHA-256 = 4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358
scope = SCIENTIFIC_CHALLENGE_STAGE_A_RAW_EXECUTION_ONLY
public_v0_5_6_doi = 10.5281/zenodo.22293061
consumed = false
start_stage_a = ABSENT
RUN_AUTHORIZATION_IDENTITY = PASS
RUN_AUTHORIZATION_CONSUMED = NO
```

Original file was not modified.

## 5. Runtime verification

Required:

```
ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
NumPy = 2.2.0
```

Observed on this VM:

```
docker/podman/nerdctl/ctr/skopeo/apptainer = ABSENT
/var/run/docker.sock = ABSENT
GHCR manifest anonymous = HTTP 401
GHCR manifest with GitHub CLI token = HTTP 401
host NumPy = 2.4.4 (not the frozen runtime)
image pulled = NO
inside-runtime CAE/Lilotane/pandaPIparser/IPC HEAD checks = NOT_PERFORMED
rebuild = NOT ATTEMPTED
```

Host Python was not used as a substitute for the immutable runtime.

`STAGE_A_RUNTIME_PRECHECK = FAIL`
`STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE`

## 6. PRESTART tests

Not run. The packet requires the 48/48 public suite inside the immutable runtime. Sentinel DOI was not substituted with the real DOI.

## 7. External executor-wrapper identity/conformance

Not executed. Wrapper construction and sentinel fixtures require the pinned runtime (NumPy 2.2.0 and CAE at `9164499c60ebe5ced32f0005009fc4e72aca77ca`). No `stage_a_executor_v0.5.6.py` was started as a decisive surface.

## 8. START_STAGE_A / authorization consumption

```
START_STAGE_A.json = ABSENT
RUN_AUTHORIZATION_CONSUMPTION.json = ABSENT
PRESTART_STAGE_A_READY.json = NOT CREATED
authorization_consumed = false
```

## 9–14. Real DOI seeds, Track A, IPC split, Lilotane baseline, Track B

Not started. PRESTART failure forbids real-DOI derivation and planner execution.

## 15. Incident ledger

Runtime identity failure during PRESTART. No scientific unit began.

## 16. Stage-boundary counters

```
candidate_selection_count = 0
held_out_count = 0
external_label_join_count = 0
scoring_count = 0
verdict_count = 0
```

## 17–18. Stage-A manifest / durable evidence

This branch stores PRESTART STOP evidence only. No Stage-A raw ZIP was produced.

## 19. Deviations / STOPs

Terminal:

```
STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE
```

Gates 9–12 were not independently completed because they require the retrieved runtime. They are recorded as NOT_RUN / NOT_RESOLVED, not as PASS.

Author action to re-issue Stage A on a VM that can `docker pull` the digest-pinned GHCR image (linux/amd64) with `read:packages` access, then re-run the same packet. Do not consume this RUN_AUTHORIZATION until PRESTART_STAGE_A_READY = YES.

## 20. Final strings

```
STOP_STAGE_A_RUNTIME_IDENTITY_FAILURE
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
CANDIDATE_SELECTION = NOT AUTHORIZED
HELD_OUT_ABLATION = NOT AUTHORIZED
EXTERNAL_LABEL_SCORING = NOT AUTHORIZED
HYPOTHESIS_VERDICT = NOT AUTHORIZED
STOP.
```

## REPORT IDENTITY

```
OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: SCIENTIFIC_STAGE_A_RAW_EXECUTION
RUN_ID: OTT-v0.5.6-SCA-20260904T061127Z-40797FC6
MESSAGE_ID: OTT-v0.5.6-SCA-20260904T061127Z-40797FC6-M001
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T06:13:30Z
AGENT: Cursor Agent cursor-grok-4.6
PARENT_P2B_RUN_ID: OTT-v0.5.6-P2B-20260904T055902Z-1D12E2EF
PARENT_P2B_COMMIT: 27f157d6767e77bdb9a07d63e742aec28e100793
PUBLIC_V0_5_6_DOI: 10.5281/zenodo.22293061
PUBLIC_PROTOCOL_ZIP_SHA256: 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PUBLIC_PROTOCOL_ROOT_SHA256: b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
RUN_AUTHORIZATION_SHA256: 4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358
RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
END_OTT_REPORT_SIGNATURE
```
