---
document_type: OTT_v0.5.5_STAGE_A_STOP_REPORT
document_id: OTT-v0.5.5-SCA-20260904T021650Z-0E895732-M002
run_id: OTT-v0.5.5-SCA-20260904T021650Z-0E895732
created_at_utc: 2026-09-04T02:24:07Z
protocol_version: v0.5.5
stage: SCIENTIFIC_CHALLENGE_STAGE_A_RAW_EXECUTION
final_verdict: STOP_STAGE_A_EXECUTION_PATH_AMBIGUOUS
---

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.5
STAGE: SCIENTIFIC_CHALLENGE_STAGE_A_RAW_EXECUTION
RUN_ID: OTT-v0.5.5-SCA-20260904T021650Z-0E895732
MESSAGE_ID: OTT-v0.5.5-SCA-20260904T021650Z-0E895732-M002
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T02:24:07Z
AGENT: Cursor Agent cursor-grok-4.6 bc-a44d5fad-cc3c-4213-86ff-505b70bdd621
PARENT_RUN_ID: OTT-v0.5.5-FFEC-20260904T020254Z-6A960332
RUN_AUTHORIZATION: ISSUED_FOR_STAGE_A_ONLY
RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
INPUT_ZIP_SHA256: a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018
END_OTT_REPORT_SIGNATURE

# OTT v0.5.5 — SCIENTIFIC CHALLENGE STAGE A REPORT

## 1. Verdict

**STOP_STAGE_A_EXECUTION_PATH_AMBIGUOUS**

Identity gates for the sealed ZIP, PREFREEZE root, 27/27 manifest, 7/7 contracts, local runtime digest, and runtime fingerprint all matched. The sealed v0.5.5 package does not unambiguously define how to invoke Stage A (no commands/scripts; PREFREEZE prohibition; missing `public_v0.5_DOI`). No raw scientific computation was started. No candidate selection, ablation, scoring, or hypothesis verdict occurred.

## 2. Report identity

| Field | Value |
|---|---|
| RUN_ID | `OTT-v0.5.5-SCA-20260904T021650Z-0E895732` |
| MESSAGE_ID | `OTT-v0.5.5-SCA-20260904T021650Z-0E895732-M002` |
| PARENT_RUN_ID | `OTT-v0.5.5-FFEC-20260904T020254Z-6A960332` |
| PACKET | `OTT_v0.5.5_SCIENTIFIC_STAGE_A_RUN_AUTHORIZATION_CURSOR_PACKET_2477.md` |
| PACKET_SHA256 | `f995cc40b07000b8a97e420bbfc1e9ce79b32087e31ead8bd7fb7c751d4f3262` |
| PACKET_BYTES | 15187 |
| CREATED_AT_UTC | `2026-09-04T02:24:07Z` |

## 3. Run authorization identity

Cursor packet status: `RUN_AUTHORIZATION = ISSUED_FOR_STAGE_A_ONLY`.

Sealed-tree authorization object: **absent**. Only `protocol/RUN_AUTHORIZATION.template.json` exists, with `public_v0.5_DOI: null`. Contract `test_not_frozen_and_no_run_authorization` requires `RUN_AUTHORIZATION.json` not to exist. This packet therefore cannot be executed as a frozen Gate-1 authorization against the sealed archive as written.

Scope consumed: none. Authorization is **not** consumed for Stage A because Stage A did not run.

```text
CANDIDATE_SELECTION = NOT AUTHORIZED
HELD_OUT_ABLATIONS = NOT AUTHORIZED
EXTERNAL_LABEL_SCORING = NOT AUTHORIZED
H1/H2/H3/H4_VERDICT = NOT AUTHORIZED
PUBLICATION = NOT AUTHORIZED
```

## 4. Runtime identity

| Field | Value |
|---|---|
| Required ref | `ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8` |
| Local RepoDigest | EXACT_MATCH (same digest) |
| Local image ID / config | `sha256:204e3b2dd396767d671e132de2ec76634886fd14f08b811d64c623659d353f86` |
| Fresh `docker pull` by digest this host | FAILED (`manifest unknown`); GHCR HTTP 403 `DENIED` / `invalid token` |
| Fingerprint JSON SHA-256 | `8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd` EXACT_MATCH |
| Fingerprint root | `166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271` EXACT_MATCH (12/12 files) |
| Platform | linux/amd64 (host `x86_64`) |
| Runner | Cursor VM hostname `cursor`; Docker Engine 29.8.0 storage-driver vfs |
| Rebuild | NOT DONE |

Local digest/fingerprint were inspected read-only. No scientific process was launched in the image. GHCR credentials used for the failed pull were wiped (`docker logout` / no `/root/.docker/config.json`).

## 5. Sealed protocol identity

| Field | Value |
|---|---|
| ZIP | `OTT_External_Blind_Challenge_v0.5.5_PREFREEZE_EXECUTION_CLOSURE.zip` |
| ZIP SHA-256 | `a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018` EXACT_MATCH |
| ZIP bytes | 47137 |
| PREFREEZE_ROOT_SHA256 | `db6e1d45946b02c2226eb2a08c1ac431dfe74ff1d5241eec52ecd6eb55b7692b` EXACT_MATCH |
| MANIFEST | 27/27 |
| CONTRACT | 7/7 PASS (`pytest tests/test_prefreeze_contract.py`) |
| Sealed `oci_digest` | `null` (prefreeze; freeze digest lives outside this archive) |

## 6. Frozen Stage-A execution map

**STAGE_A_EXECUTION_MAP = NOT_FROZEN_AND_UNAMBIGUOUS**

Commands taken from the sealed package for Stage A: **none**.

The only executable command in the sealed package is the prefreeze `docker build` in `BUILD_INSTRUCTIONS_FOR_KIMI.md`, which is a runtime-closure builder role and explicitly forbids decisive science.

Adapter specs describe future science:

- CAE: 32×128, seed `SHA256(public_v0.5_DOI \|\| CAE_commit \|\| system \|\| condition \|\| replicate_index)`
- IPC: split `SHA256(public_v0.5_DOI \|\| domain \|\| relative_problem_path)`, then baseline feasibility, then development candidate selection

Those are specifications, not invocation entrypoints. `public_v0.5_DOI` does not exist (`RELEASE_NOTES.md`: “future public v0.5 DOI”). Inventing a DOI, harness, or “run CAE tests as 32×128” mapping is forbidden.

Image inspection (`/opt/ott/sources/CAE/test/`): CAE unit tests plus `runner.py` (unbounded metric suite). No file matches `32×128` / `public_v0.5_DOI` / `DOI-salt`. Track B has no frozen subcommand that stops before candidate selection.

## 7. Prospective start boundary

**NOT CROSSED.** Execution-map hash/config freeze before decisive computation was not performed because no frozen command exists. No Stage-A start timestamp for science was issued.

## 8. CAE raw execution

**NOT RUN**

## 9. IPC/raw external-track execution

**NOT RUN** (`NOT APPLICABLE UNDER SEALED PROTOCOL` as an executable Stage-A entrypoint)

## 10. Seed/split derivation evidence

**NOT RUN** — `public_v0.5_DOI` is null; deriving seeds would invent a salt.

## 11. Raw output inventory

No scientific raw outputs. This STOP package contains only identity/gate/stop documents.

## 12. Retry/incident ledger

| UTC | Event |
|---|---|
| 2026-09-04T02:16:50Z | RUN_ID created; packet hashed |
| 2026-09-04T02:16:50Z | ZIP SHA-256 match; Docker started |
| 2026-09-04T02:17:xxZ | Fresh unzip MANIFEST 27/27; contracts 7/7 |
| 2026-09-04T02:18:xxZ | `docker pull` by digest: login succeeded, `manifest unknown` |
| 2026-09-04T02:18:xxZ | GHCR manifests API: HTTP 403 DENIED invalid token |
| 2026-09-04T02:19–02:23Z | Read-only image inspect; fingerprint 12/12 recomputed EXACT_MATCH; no Stage-A scripts |
| 2026-09-04T02:23:xxZ | GHCR docker credentials wiped |

No protocol-defined scientific retry. No unfrozen retry of science.

## 13. Durable evidence location

Public HTTPS (no sealed ZIP, no blind labels, no scientific outputs):

Branch `cursor/ott-v055-stage-a-stop-d621`, directory `evidence/stage-a-stop/`.

Do not merge to `main`.

## 14. Scientific boundary audit

```text
CANDIDATE_SELECTION = NOT RUN
HELD_OUT_ABLATIONS = NOT RUN
EXTERNAL_LABEL_SCORING = NOT RUN
HYPOTHESIS_VERDICT = NOT ISSUED
PUBLICATION = NOT RUN
SCIENTIFIC_CHALLENGE_STAGE_A = NOT COMPLETE
RAW_PROSPECTIVE_OUTPUTS = NOT CREATED
```

Supporting precondition facts (not a second verdict code): sealed archive remains PREFREEZE; Gate 0 public frozen protocol + DOI unpublished; `RUN_AUTHORIZATION.json` absent.

## 15. Final strings

```text
STOP_STAGE_A_EXECUTION_PATH_AMBIGUOUS
RUN_AUTHORIZATION = ISSUED_FOR_STAGE_A_ONLY (NOT CONSUMED)
SCIENTIFIC_CHALLENGE_STAGE_A = NOT RUN
RAW_PROSPECTIVE_OUTPUTS = NOT CREATED
CANDIDATE_SELECTION = NOT RUN
HELD_OUT_ABLATIONS = NOT RUN
EXTERNAL_LABEL_SCORING = NOT RUN
HYPOTHESIS_VERDICT = NOT ISSUED
PUBLICATION = NOT RUN
```

## 16. REPORT IDENTITY

| Field | Value |
|---|---|
| RUN_ID | `OTT-v0.5.5-SCA-20260904T021650Z-0E895732` |
| MESSAGE_ID | `OTT-v0.5.5-SCA-20260904T021650Z-0E895732-M002` |
| PARENT_RUN_ID | `OTT-v0.5.5-FFEC-20260904T020254Z-6A960332` |
| CREATED_AT_UTC | `2026-09-04T02:24:07Z` |
| STOP | `STOP_STAGE_A_EXECUTION_PATH_AMBIGUOUS` |

STOP.
