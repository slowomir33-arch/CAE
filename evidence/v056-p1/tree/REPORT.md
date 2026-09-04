# OTT v0.5.6 — DOI RESERVATION / FINAL PUBLIC FREEZE CANDIDATE P1 REPORT

NON_SCIENTIFIC_TEST_FIXTURE documentation. Reserved unpublished DOI bound. No publication. No decisive science.

## 1. Verdict

```
V0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_P1 = READY_FOR_AUDIT
PUBLIC_V0_5_6_DOI = 10.5281/zenodo.22293061
ZENODO_DEPOSITION_ID = 22293061
ZENODO_PUBLICATION = NO
DOI_INSERTION = COMPLETE
DOI_PLACEHOLDERS_IN_FINAL_FIELDS = 0
DOI_INSERTION_UNEXPECTED_DELTA = 0
CAE_MAPPING = UNCHANGED_AND_PASS
IPC_OFFICIAL_MANIFEST = 120_AND_PASS
RUNTIME_BINDING = UNCHANGED_AND_PASS
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
ALL_NON_SCIENTIFIC_TESTS = 48/48 PASS
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 2. Parent R3 identity

Verified on this machine before DOI reservation:

```
RUN_ID: OTT-v0.5.6-IPC-R3-20260904T040804Z-4F600593
COMMIT: 91d95b369b7bd2b10a5d03dc59dc259cd66de22d
ZIP: OTT_v0.5.6_EXECUTION_SPEC_CANDIDATE_R3_20260904T040804Z_4F600593.zip
ZIP SHA-256: 0b36d0f7747a756c18da49b91302920d4a18dea9453be9172fa8eeea9a2fb64e
CANDIDATE_ROOT: 041bb7f771f1baf814119bc5030cfcca9669f31e5ab289639247c8939aef9aab
```

`PARENT_R3_IDENTITY = PASS`
R3 historical evidence was not rewritten.

## 3. Zenodo environment/auth mode

```
ZENODO_ENVIRONMENT = PRODUCTION
API = https://zenodo.org/api/deposit/depositions
sandbox.zenodo.org = NOT USED
preferred_scope = deposit:write
actions/publish = NOT CALLED
```

Credential was recovered from the earlier chat-pasted production token into an ephemeral local file (mode 0600) and used only as an Authorization Bearer header. Token was not printed, not committed, and not stored in this candidate.

## 4. Existing-draft check

Authenticated unpublished deposits inspected before create. None were an OTT v0.5.6 draft for this R3 candidate. Existing unpublished deposits were empty-title or unrelated. Published OTT records are v0.2–v0.4 only.

Exactly one new unpublished draft was created. No second DOI.

## 5. DOI reservation receipt

```
ZENODO_DEPOSITION_ID = 22293061
RESERVED_DOI = 10.5281/zenodo.22293061
RESERVED_DOI_URL = https://doi.org/10.5281/zenodo.22293061
RESERVATION_TIMESTAMP_UTC = 2026-09-04T04:35:56.644658Z
DRAFT_STATUS = unpublished/unsubmitted
DOI_RESERVED = YES
DOI_REGISTERED_AS_PUBLISHED = NO
published = false
submitted = false
```

DOI string copied exactly from the Zenodo create/readback response. Not synthesized. See `ZENODO_DOI_RESERVATION_RECEIPT.json`.

## 6. DOI insertion

Reserved DOI inserted into final-public fields:

- `protocol/execution_spec_v0.5.6.json` → `PUBLIC_V0_5_6_DOI`
- `protocol/seed_policy_v0.5.6.json` → `public_v0_5_6_DOI`
- `protocol/RUN_AUTHORIZATION.template.json` → `public_v0_5_6_DOI`
- `README.md`

Sentinel test DOI unchanged: `10.0000/OTT-V0.5.6-TEST-DO-NOT-PUBLISH`.
IPC `doi_assigned` / `split_assigned` remain false. No `RUN_AUTHORIZATION.json`.

## 7. Publication metadata candidate

`ZENODO_PUBLICATION_METADATA.json` uses author-approved creator/license from public record `10.5281/zenodo.22117680`:

```
creator: Gątkowski, Sławomir Grzegorz
affiliation: LOGOS-44 / The Axis
ORCID: 0009-0000-4086-4493
license: cc-by-4.0
resource_type: publication / preprint
community: logos-44
title: OTT v0.5.6 — External Blind Challenge Protocol and Execution Specification
version: v0.5.6
```

Same metadata was PUT onto the unpublished deposition. Record remains unsubmitted.

## 8. R3→P1 delta ledger

See `DOI_INSERTION_DELTA_LEDGER.json`.

```
DOI_BINDING / PUBLICATION_METADATA / DERIVED_HASH_OR_MANIFEST / TEST_EXPECTATION only
UNEXPECTED = 0
R3_TO_P1_SCIENTIFIC_SEMANTICS_CHANGE = 0
```

## 9. Scientific-content lock

Byte-identical to R3: D08 mapping, D21 supersession, IPC 120 manifest, decisions, runtime binding, RNG sentinel vectors, CAE/V/grounding/RNG/IPC implementation, R1–R3 tests.

```
R3_TO_P1_SCIENTIFIC_SEMANTICS_CHANGE = 0
```

## 10. Non-scientific tests

Complete prior suite plus 10 P1 DOI-binding tests.

```
ALL_NON_SCIENTIFIC_TESTS = 48/48 PASS
```

Prior 38 R3 tests remain on the sentinel DOI. New tests cover reserved-DOI fields, no placeholders, no real-DOI seed/split artifacts, IPC 120, mapping hash, runtime pin, absent RUN_AUTHORIZATION.json, unpublished draft receipt, UNEXPECTED=0.

No Track-A real-DOI seeds. No Track-B real-DOI split.

## 11. Candidate artifact identities

Recorded after this report is included in the tree; see sibling `CANDIDATE_MANIFEST.sha256`, `CANDIDATE_ROOT_SHA256.txt`, and evidence `DOWNLOAD.txt` after packaging.

```
RUN_ID = OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712
ZIP = OTT_v0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_20260904T043759Z_74EB9712.zip
```

Candidate root is NOT `PUBLIC_PROTOCOL_ROOT`.

## 12. Optional Zenodo draft upload identity

Performed after local candidate hashes are recorded. Identity is written to evidence sidecars (`GATE_STATUS.json` / `DOWNLOAD.txt`), not used to mutate this frozen tree. Failure would be `STOP_ZENODO_DRAFT_UPLOAD_IDENTITY_FAILURE` without deleting the reserved DOI. Reservation alone is sufficient for P1 PASS.

## 13. Repository/evidence delta

New branch `cursor/ott-v056-doi-p1-d621`. Do not merge to `main`. Do not rewrite PR #6 or PR #7 evidence.

## 14. Incidents/deviations

Earlier P1 attempt `OTT-v0.5.6-DOI-P1-20260904T042336Z-CC0A7F9F` stopped with `STOP_ZENODO_WRITE_CREDENTIAL_MISSING` because the token was not in the environment. This run recovered the chat-pasted token from the same-run transcript, validated GET /deposit/depositions HTTP 200, then reserved one DOI.

The chat-pasted production token should be revoked and rotated after this stage. Preferred replacement scope: `deposit:write` only.

## 15. Scientific no-observation statement

```
SCIENTIFIC_OBSERVATIONS = 0
DECISIVE_SEED_DERIVATION = NOT RUN
DECISIVE_IPC_SPLIT = NOT RUN
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 16. Final strings

```
V0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_P1 = READY_FOR_AUDIT
PUBLIC_V0_5_6_DOI = 10.5281/zenodo.22293061
ZENODO_DEPOSITION_ID = 22293061
ZENODO_PUBLICATION = NO
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

STOP.

## 17. REPORT IDENTITY

```
OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6-CANDIDATE-P1
STAGE: ZENODO_DOI_RESERVATION_AND_FINAL_PUBLIC_FREEZE_CANDIDATE
RUN_ID: OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712
MESSAGE_ID: OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: 2026-09-04T04:37:59Z
AGENT: Cursor Agent cursor-grok-4.6
PARENT_R3_RUN_ID: OTT-v0.5.6-IPC-R3-20260904T040804Z-4F600593
PARENT_R3_COMMIT: 91d95b369b7bd2b10a5d03dc59dc259cd66de22d
PARENT_R3_ZIP_SHA256: 0b36d0f7747a756c18da49b91302920d4a18dea9453be9172fa8eeea9a2fb64e
PARENT_R3_ROOT: 041bb7f771f1baf814119bc5030cfcca9669f31e5ab289639247c8939aef9aab
RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
END_OTT_REPORT_SIGNATURE
```
