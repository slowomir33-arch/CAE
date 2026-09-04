# OTT v0.5.6 — IPC MEMBERSHIP CORRECTION / CANDIDATE R3 REPORT

NON_SCIENTIFIC_TEST_FIXTURE documentation. No DOI. No publication. No decisive science.

## 1. Verdict

```
V0.5.6_EXECUTION_SPEC_CANDIDATE_R3 = READY_FOR_AUDIT
D21_IPC_OFFICIAL_MANIFEST = PASS
CAE_MAPPING = COMPLETE_AND_UNAMBIGUOUS
ROVER_GTOHP = 30
SATELLITE_GTOHP = 20
TRANSPORT = 40
WOODWORKING = 30
IPC_OFFICIAL_TOTAL = 120
WOODWORKING_NON_IPC_EXTRAS = 10 EXCLUDED
ALL_NON_SCIENTIFIC_TESTS = 38/38 PASS
SCIENTIFIC_OBSERVATIONS = 0
PUBLIC_V0_5_6_DOI = NOT RESERVED
DECISIVE_IPC_SPLIT = NOT RUN
PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 2. Parent R2 identity

```
PARENT_R2_COMMIT = bdfa80f5ca2203482480bcc29b2c77c4237707e0
PARENT_R2_ZIP = OTT_v0.5.6_EXECUTION_SPEC_CANDIDATE_R2_20260904T033323Z_448BB00F.zip
PARENT_R2_ZIP_SHA256 = 4e7d8b372764a34fe1f76071d024a28af17cdabbded377b22741f8a31a597034
PARENT_R2_CANDIDATE_ROOT = 98238e25b2ec71724666107f6b51612bff9bbba087daa380f17a6d5cef09de25
ARTIFACT_RUN_ID = OTT-v0.5.6-CMCR2-20260904T033323Z-448BB00F
LATER_STOP_REPORT_RUN_ID = OTT-v0.5.6-CMCR2-20260904T040331Z-84CFREAF
PARENT_R2_IDENTITY = PASS
```

R2 historical evidence was not rewritten.

## 3. D21 audit finding

R2 D21 required Woodworking=40 and exclusion of `further-instances-not-used-in-ipc`, which is inconsistent on the pinned tree.

## 4. Authoritative IPC source evidence

Pinned `panda-planner-dev/ipc2020-domains@9e313248244a0a13302ae262f42ef446f43e4182`.
README distinguishes Woodworking repository population 40 from IPC 2020 evaluation population 30. Ten extras live under `total-order/Woodworking/further-instances-not-used-in-ipc/`.

## 5. D21 supersession record

`protocol/D21_SUPERSESSION_v0.5.6.json`
Original D21 decision text (Woodworking=40, TOTAL=130) is preserved in `protocol/decisions_v0.5.6.json`.
`D21_CORRECTION_1 = AUDITOR_PRE_RESULT_CORRECTION_OF_BENCHMARK_MEMBERSHIP`

## 6. Official four-domain membership counts

Rover-GTOHP 30, Satellite-GTOHP 20, Transport 40, Woodworking 30, TOTAL 120.

## 7. Woodworking excluded-extra proof

10 excluded rows whose canonical path is under `further-instances-not-used-in-ipc/`. None of those paths are eligible. Membership uses directory/population semantics, not numeric filename inference.

## 8. Parser acceptance audit

All 120 eligible rows have `parse_accepted=true` under `pandaPIparser@95bbe291c5bdb9fb517c1ad55f5136d45450c644`. File SHA-256 values were already verified in R2 against the runtime tree (0 mismatches); eligible set is unchanged.

## 9. R2→R3 delta ledger

See `R2_TO_R3_DELTA_LEDGER.json`. Expected protocol delta only: Woodworking 40→30, total 130→120, extras excluded 10.
D08/D19/D20/D22/D23/D24 implementation files are byte-identical to R2.
`STOP_R3_UNEXPECTED_SCIENTIFIC_DELTA` was not raised.

## 10. Regression tests

Prior R2 suite plus 7 new D21 tests: **38 passed**.
New tests: official counts, other-domain lock, Woodworking=30, extras ineligible, Woodworking=40 regression, parser acceptance, supersession document.

## 11. Preservation of D08/D19/D20/D22/D23/D24

Unchanged and still PASS. Mapping file byte-identical. RNG vectors byte-identical. V/grounding/wrapper byte-identical.

## 12. Candidate R3 artifact identities

See sibling `CANDIDATE_ROOT_SHA256.txt`, `CANDIDATE_MANIFEST.sha256`, and evidence `DOWNLOAD.txt` after packaging.

## 13. Repository delta

New branch `cursor/ott-v056-ipc-r3-d621`. Does not merge to `main`. Does not rewrite R2 evidence.

## 14. Deviations/incidents

None. Eligible problem set is the same 120 files as R2 official-root observation; only the required-count table and status changed from STOP to PASS.

## 15. Scientific no-observation statement

```
SCIENTIFIC_OBSERVATIONS = 0
PUBLIC_V0_5_6_DOI = NOT RESERVED
DECISIVE_IPC_SPLIT = NOT RUN
PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 16. Final strings

```
V0.5.6_EXECUTION_SPEC_CANDIDATE_R3 = READY_FOR_AUDIT
D21_IPC_OFFICIAL_MANIFEST = PASS
CAE_MAPPING = COMPLETE_AND_UNAMBIGUOUS
DECISIONS_IMPLEMENTED = 24/24
ROVER_GTOHP = 30
SATELLITE_GTOHP = 20
TRANSPORT = 40
WOODWORKING = 30
IPC_OFFICIAL_TOTAL = 120
```

STOP.

## 17. REPORT IDENTITY

See OTT_REPORT_SIGNATURE in the accompanying message.
