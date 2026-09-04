# OTT v0.5.6 — PUBLICATION VERIFICATION / POST-PUBLICATION AUTHORIZATION REPORT

## 1. Verdict

```
V0.5.6_PUBLICATION_VERIFICATION = PASS
FINAL_PUBLIC_PROTOCOL_FREEZE = PASS
PUBLIC_V0_5_6_DOI = 10.5281/zenodo.22293061
ZENODO_CONCEPT_DOI = 10.5281/zenodo.22293060
CONCEPT_DOI_USED_FOR_SCIENTIFIC_HASHING = NO
PUBLIC_PROTOCOL_ZIP_SHA256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PUBLIC_PROTOCOL_ROOT_SHA256 = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
POST_PUBLICATION_RUN_AUTHORIZATION = ISSUED_FOR_STAGE_A_ONLY
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
```

Unauthenticated public reads only. No Zenodo credential. No Stage A.

## 2. Parent P1/P2A identities

P1 PR #8 / `57c7b561bba4cb1fa8ab0c1e6db037658025f7be` / `OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712`
ZIP SHA-256 `41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f`
candidate root `b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516`

P2A PR #10 / `8a8ecd0d8b9fd387b2eea3192af0537357dc4b7f` / `OTT-v0.5.6-P2A-20260904T054511Z-DA150E60`
`P2A_PREPUBLICATION_SECURITY_RELOCK = PASS`
`AUTHOR_PUBLISH_WINDOW = OPEN`

`PARENT_P1_IDENTITY = PASS`
`PARENT_P2A = PASS`

## 3. Public DOI resolution

```
https://zenodo.org/records/22293061 = HTTP 200
https://zenodo.org/api/records/22293061 = HTTP 200
https://doi.org/10.5281/zenodo.22293061 → https://zenodo.org/records/22293061 (HTTP 200)
https://doi.org/10.5281/zenodo.22293060 → https://zenodo.org/records/22293061 (HTTP 200)
version DOI = 10.5281/zenodo.22293061
concept DOI = 10.5281/zenodo.22293060
record id = 22293061
status = published
state = done
access = open
```

Concept DOI landing on the latest version record page is expected lineage behavior. Scientific hashing authority remains the version DOI only.

## 4. Public Zenodo metadata

```
title = OTT v0.5.6 — External Blind Challenge Protocol and Execution Specification
version = v0.5.6
creator = Gątkowski, Sławomir Grzegorz
ORCID = 0009-0000-4086-4493
affiliation = LOGOS-44 / The Axis
license = cc-by-4.0
access = open
DOI = 10.5281/zenodo.22293061
```

Description still states this is a preregistered protocol/execution specification containing no challenge results, no decisive CAE 32×128, and no DOI-derived IPC split / baseline / candidate-selection / scoring / verdict.

P1 notes text still contains the historical phrase `RECORD UNPUBLISHED` because the author did not edit metadata at publish (as required). Publication is established by Zenodo `status=published`, public HTTP 200, and DOI resolution — not by rewriting notes.

`PUBLIC_METADATA = PASS`

## 5. Public fileset

Exactly one public file:

```
OTT_v0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_20260904T043759Z_74EB9712.zip
size = 58243
zenodo checksum = md5:9c142861f44030400243a2eb3465f793
id = 621ed097-a818-4479-af65-0220f0b7c0ac
download = https://zenodo.org/api/records/22293061/files/OTT_v0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_20260904T043759Z_74EB9712.zip/content
```

`PUBLIC_FILESET = EXACT`

## 6. Published ZIP byte identity

```
PUBLIC_ZIP_BYTES = 58243
PUBLIC_ZIP_SHA256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
byte identity to P1/P2A = YES
```

Downloaded without authentication from the public record.

## 7. Manifest verification

Every `CANDIDATE_MANIFEST.sha256` row was hashed against extracted bytes.

```
rows = 35
matches = 35
PUBLIC_MANIFEST = 100_PERCENT_PASS
```

## 8. PUBLIC_PROTOCOL_ROOT derivation

Algorithm (P1): SHA-256 of the `CANDIDATE_MANIFEST.sha256` file bytes, after 100% row verification.

```
RECOMPUTED_PUBLIC_PROTOCOL_ROOT = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
PUBLIC_PROTOCOL_ROOT_SHA256 = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
```

This is the first stage authorized to use `PUBLIC_PROTOCOL_ROOT` for this candidate.

## 9. Publication receipt

```
publication_timestamp_utc = 2026-09-04T05:49:13.619399Z
updated_timestamp_utc = 2026-09-04T05:49:13.814694Z
publication_date = 2026-09-04
public_read_authenticated = false
```

See `PUBLICATION_VERIFICATION_RECEIPT.json`.

## 10. Runtime binding

```
runtime_immutable_ref = ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
runtime_digest = sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
runtime_fingerprint_root = 166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271
```

Unchanged from P1/P2A. Not executed in P2B.

## 11. RUN_AUTHORIZATION creation

Created **after** publication verification PASS. Not part of the published protocol root.

```
document = OTT_RUN_AUTHORIZATION
authorization_scope = SCIENTIFIC_CHALLENGE_STAGE_A_RAW_EXECUTION_ONLY
public_v0_5_6_doi = 10.5281/zenodo.22293061
RUN_AUTHORIZATION_SHA256 = 4c6d8aff18dac5fdaa55a8a5733244b96dc49761da88efc4827388622271d358
consumed = false
```

Concept DOI does not appear in `RUN_AUTHORIZATION.json`.

## 12. Temporal authorization gate

```
publication_timestamp_utc = 2026-09-04T05:49:13.619399Z
authorization_timestamp_utc = 2026-09-04T05:59:14.006785Z
authorization_timestamp_utc > publication_timestamp_utc = PASS
```

## 13. Randomization non-leak

No real DOI-derived seed list, IPC split assignments, baseline ledger, candidate selection, held-out outputs, scores, verdicts, or `START_STAGE_A.json` in the public ZIP. Sentinel vectors remain sentinel.

```
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
```

P2B did not generate them.

## 14. Scientific execution boundary

```
RUN_AUTHORIZATION = ISSUED_FOR_STAGE_A_ONLY
RUN_AUTHORIZATION_CONSUMED = NO
START_STAGE_A = ABSENT
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
```

P2B did not run Stage A. A separate Stage-A executor packet is required after auditor review.

## 15. Evidence identities

Branch `cursor/ott-v056-p2b-verify-5ef6`. Do not merge to `main`.

HTTP methods used: GET, HEAD. Authorization header: never. Zenodo mutation: none.

## 16. Incidents/deviations

None that fail a gate. Notes field retains P1 unpublished wording by author non-edit at publish.

## 17. Final strings

```
V0.5.6_PUBLICATION_VERIFICATION = PASS
FINAL_PUBLIC_PROTOCOL_FREEZE = PASS
POST_PUBLICATION_RUN_AUTHORIZATION = ISSUED_FOR_STAGE_A_ONLY
RUN_AUTHORIZATION_CONSUMED = NO
SCIENTIFIC_OBSERVATIONS = 0
STOP.
```

## 18. REPORT IDENTITY

```
OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6
STAGE: PUBLICATION_VERIFICATION_AND_POSTPUBLICATION_RUN_AUTHORIZATION
RUN_ID: OTT-v0.5.6-P2B-20260904T055902Z-1D12E2EF
MESSAGE_ID: OTT-v0.5.6-P2B-20260904T055902Z-1D12E2EF-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: 2026-09-04T05:59:02Z
AGENT: Cursor Agent cursor-grok-4.6
PARENT_P1_RUN_ID: OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712
PARENT_P1_COMMIT: 57c7b561bba4cb1fa8ab0c1e6db037658025f7be
PARENT_P1_ZIP_SHA256: 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PARENT_P1_ROOT: b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
PARENT_P2A_RUN_ID: OTT-v0.5.6-P2A-20260904T054511Z-DA150E60
ZENODO_RECORD_ID: 22293061
PUBLIC_V0_5_6_DOI: 10.5281/zenodo.22293061
ZENODO_CONCEPT_DOI: 10.5281/zenodo.22293060
RUNTIME_DIGEST: sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
END_OTT_REPORT_SIGNATURE
```
