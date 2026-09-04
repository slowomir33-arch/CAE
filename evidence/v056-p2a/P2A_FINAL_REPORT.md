# OTT v0.5.6 — P2A PREPUBLICATION SECURITY RELOCK REPORT

## 1. Verdict

```
P2A_PREPUBLICATION_SECURITY_RELOCK = PASS
AUTHOR_PUBLISH_WINDOW = OPEN
ZENODO_PUBLICATION = NO
PARENT_P1_IDENTITY = PASS
DRAFT_FILE_BYTE_IDENTITY = PASS
DRAFT_METADATA_IDENTITY = PASS
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

Authenticated re-read of unpublished production draft `22293061` with runtime secret `ZENODO_P2A_WRITE_TOKEN` only. Exact P1 file and metadata identity. No publish call.

## 2. Parent P1 identity

PR #8 / commit `57c7b561bba4cb1fa8ab0c1e6db037658025f7be`:

```
ZIP bytes = 58243
ZIP SHA-256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
CANDIDATE_ROOT = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
DOI = 10.5281/zenodo.22293061
DEPOSITION = 22293061
```

`PARENT_P1_IDENTITY = PASS`

## 3. Security relock

Author stated: old P1 token revoked. Use only `ZENODO_P2A_WRITE_TOKEN` from runtime.

Observed in this VM:

```
CLOUD_AGENT_ALL_SECRET_NAMES = ZENODO_P2A_WRITE_TOKEN
ZENODO_P2A_WRITE_TOKEN in os.environ = YES
ZENODO_TOKEN in os.environ = NO
token recovered from chat/transcript/history = NO
old credential used = NO
deposit:actions used = NO
actions/publish called = NO
HTTP methods = GET only
```

Independent cryptographic proof that the old Zenodo token is dead was **not** obtained, because checking it would require using the old credential. Author declaration is recorded as `REVOKED_BY_AUTHOR`.

New-token scope intent is `deposit:write` only (author-stated). This stage exercised GET deposit + GET file download only.

## 4. Draft file re-read

Authenticated file list on deposition `22293061`:

```
files = [{"filename": "OTT_v0.5.6_FINAL_PUBLIC_FREEZE_CANDIDATE_20260904T043759Z_74EB9712.zip", "size": 58243, "checksum": "9c142861f44030400243a2eb3465f793", "id": "621ed097-a818-4479-af65-0220f0b7c0ac"}]
DRAFT_FILESET = EXACT
downloaded bytes = 58243
downloaded SHA-256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
candidate root inside ZIP = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
DRAFT_FILE_BYTE_IDENTITY = PASS
```

## 5. Draft metadata re-read

```
title = OTT v0.5.6 — External Blind Challenge Protocol and Execution Specification
version = v0.5.6
reserved DOI = 10.5281/zenodo.22293061
creator = Gątkowski, Sławomir Grzegorz
ORCID = 0009-0000-4086-4493
affiliation = LOGOS-44 / The Axis
license = cc-by-4.0
state = unsubmitted
submitted = False
public /api/records/22293061 = HTTP 404
public /records/22293061 = HTTP 404
publication status = UNPUBLISHED
```

Description still states the record contains no challenge results and no DOI-derived scientific seeds / split / scoring / H1–H4 verdicts, and that the draft is unpublished with no `RUN_AUTHORIZATION.json`.

`DRAFT_METADATA_IDENTITY = PASS`

## 6. P1 scientific lock

```
CAE mapping hash = 48b3fa3059e55cde2794209db62cd00a348cc04200253525e084fff023506d52
IPC = 30 / 20 / 40 / 30 = 120
runtime digest = sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
RUN_AUTHORIZATION.json = ABSENT
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
```

No P2A byte mutation. Science remains forbidden.

## 7. Author publish window

```
AUTHOR_PUBLISH_WINDOW = OPEN
ZENODO_PUBLICATION = NO
```

P2A STOP. The next action is human and manual:

```
AUTHOR MANUAL ACTION:
Open production Zenodo deposition 22293061
verify the displayed title and file
click Publish exactly once
```

Do not edit files or metadata during this handoff. If any edit is desired, do not publish; return to auditor.

P2B is **not** authorized by this stage.

## 8. Repository

Branch `cursor/ott-v056-p2a-relock-5ef6`. Do not merge to `main`. PR #8 remains the P1 evidence branch.

## 9. Final strings

```
P2A_PREPUBLICATION_SECURITY_RELOCK = PASS
AUTHOR_PUBLISH_WINDOW = OPEN
ZENODO_PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

STOP.

## 10. REPORT IDENTITY

```
OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.6-P2A
STAGE: PREPUBLICATION_SECURITY_RELOCK_AND_AUTHOR_HANDOFF
RUN_ID: OTT-v0.5.6-P2A-20260904T054511Z-DA150E60
MESSAGE_ID: OTT-v0.5.6-P2A-20260904T054511Z-DA150E60-M001
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: 2026-09-04T05:45:11Z
AGENT: Cursor Agent cursor-grok-4.6
PARENT_P1_RUN_ID: OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712
PARENT_P1_COMMIT: 57c7b561bba4cb1fa8ab0c1e6db037658025f7be
PARENT_P1_ZIP_SHA256: 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PARENT_P1_ROOT: b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
ZENODO_DEPOSITION_ID: 22293061
PUBLIC_V0_5_6_DOI: 10.5281/zenodo.22293061
END_OTT_REPORT_SIGNATURE
```
