# OTT v0.5.6 — CAE MAPPING CLOSURE / CANDIDATE R2 REPORT

NON_SCIENTIFIC_TEST_FIXTURE documentation. No DOI. No publication. No decisive science.

## 1. Verdict

```
STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH
D08_CAE_MAPPING = RESOLVED
D19_RNG_MAPPING = IMPLEMENTED_AND_TESTED
D20_SEEDED_GROUNDING = IMPLEMENTED_AND_TESTED
D21_IPC_OFFICIAL_MANIFEST = STOP (Woodworking official-root 30 != required 40)
D22_UNMAPPED_POLICY = IMPLEMENTED_AND_TESTED
D23_PROBE_DOMAINS = IMPLEMENTED
D24_PRIMARY_CONDITIONS = RECONCILED_WITH_SEALED_ADAPTER
V_SCALAR_METRIC_DEPENDENCY = NONE
V_FULL_VECTOR_TESTS = PASS
SENTINEL_TESTS = PASS (31/31)
SCIENTIFIC_OBSERVATIONS = 0
PUBLIC_V0_5_6_DOI = NOT RESERVED
PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
V0.5.6_EXECUTION_SPEC_CANDIDATE_R2 = NOT READY_FOR_AUDIT
```

READY_FOR_AUDIT was not issued because D21 required counts are not satisfied. D08 mapping is closed. Do not invent a Woodworking-40 filter.

## 2. Parent candidate identity

```
PARENT_CANDIDATE_RUN_ID: OTT-v0.5.6-ESC-20260904T025456Z-98AAB42F
PARENT_CANDIDATE_COMMIT: eeb59077d5dbc6a9021ac847e47eb666ffd828ec
PARENT_CANDIDATE_SHA256: c29d9605f920ca83c571a5e3da963f12f4e1f0e22c196440a4093811598840a4
PARENT_CANDIDATE_ROOT: 589918bb59df31be2815aba0074d8c5ff0d4ac011f47f0eda8c723dc31b71417
PARENT_V0_5_5_ZIP_SHA256: a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018
```

Historical R1 evidence was not rewritten.

## 3. Auditor D08 resolution

V is the fraction of 128 probes whose complete frozen output vector matches between:

- `DiagramBuilder.build_path_standard_high_level_model()`
- `DiagramBuilder.build_path_standard_low_level_model()`

under one top-down / CAE_down macro intervention. Missing roots are completed as in `EvaluationEngine._process_batch_raw`. `_score_collected_results`, `MSEMetric`, `IIAMetric`, and `DCCMetric` are not used for V.

## 4. D19 RNG mapping

Runtime NumPy **2.2.0**. Digest → 8 uint32 BE words → `SeedSequence` → `spawn(128)` → per-probe `spawn(3)` = SAMPLER, GROUND, PATH.

Sentinel vectors: `protocol/NUMPY_RNG_TEST_VECTORS_v0.5.6.json` using the frozen Track-A sentinel digest.

## 5. D20 seeded grounding

`value_map.ground(name, label, rng=GROUND_RNG)` populates `micro_values` before the mapped-low path. Roundtrip failure is `STOP_GROUNDING_ROUNDTRIP_FAILURE` without resampling.

## 6. D21 IPC benchmark manifest correction

Pinned tree `panda-planner-dev/ipc2020-domains@9e313248244a0a13302ae262f42ef446f43e4182`.

Official-root parser-accepted HDDL (excluding `further-instances-not-used-in-ipc`, `other/`, domain/README/Makefile):

| Domain | Observed | Required |
|---|---:|---:|
| Rover-GTOHP | 30 | 30 |
| Satellite-GTOHP | 20 | 20 |
| Transport | 40 | 40 |
| Woodworking | 30 | 40 |
| TOTAL | 120 | 130 |

Woodworking official root has 30 problem files (00–10, 12–30; no `11.hddl`). The directory `further-instances-not-used-in-ipc/` holds 10 additional files (31–40). The repository README table lists Woodworking=40; the README text states IPC 2020 used 30 of them.

D21 requires both Woodworking=40 and exclusion of `further-instances-not-used-in-ipc`. That pair is unsatisfiable on the pinned tree. File SHA-256 of all 120 official problems was re-checked inside the accepted runtime (0 mismatches). No DOI split was performed.

## 7. D22 UNMAPPED/nonfinite behavior

UNMAPPED or unmatched declared output → `probe_match=0`. Mandatory non-finite → `INFRASTRUCTURE_FAILURE` STOP. NaN never equals, including GRN.

## 8. D23 probe generation configuration

- logic: TopDownSampler `[Operand_A, Operand_B, Carry_In, Internal_Carries]` max=2
- tracr: TopDownSampler `[token_0, token_1, token_2]` max=3
- grn: TopDownSampler `[wg_src]` max=1
- cpu_6502: InstructionSampler `[A_in,X_in,Y_in,S_in,P_in,opcode,operand]` max=7
- batch_size=1; no direct intervention on frozen outputs

## 9. D24 primary conditions/output vectors

Sealed `adapters/CAE_ADAPTER_SPEC.md` vs D24:

- Conditions: exact match for all four systems (noise excluded).
- tracr adapter `all rank_i` vs `[rank_0,rank_1,rank_2]`: `SEQ_LEN=3` naming synonym.
- cpu adapter `upstream declared register outputs` vs `[A_out,X_out,Y_out,S_out,P_out]`: byte-equal to `systems/10_cpu_6502.py` `OUTPUTS`.
- GRN `abs diff <= 1e-9` vs `rtol=0, atol=1e-9`: same scalar rule.

`STOP_CAE_ADAPTER_PRIMARY_CONDITION_CONFLICT` was not raised.

## 10. Final CAE mapping table

See `protocol/CAE_EXECUTION_MAPPING_v0.5.6.json`. Unresolved list is empty. Orientation is CAE_down only. Scalar CAE metric is NONE.

## 11. Exact-vector V implementation

`src/ott_v056/v_metric.py` and `src/ott_v056/cae_raw.py`. Full-vector Bernoulli; no componentwise average.

## 12. Sentinel/conformance tests

`PYTHONPATH` with NumPy 2.2.0: **31 passed** (R1 D01–D18 tests plus T1–T6 / D19–D24).

## 13. IPC eligible manifest

`protocol/IPC_ELIGIBLE_PROBLEM_MANIFEST_v0.5.6.json` — 120 official parser-accepted problems; 10 further-instances recorded as excluded.

## 14. Scientific delta ledger

D01–D24 classified `AUTHORIZED_PRE_RESULT_PROTOCOL_COMPLETION`. Observations before D01–D18 and before D19–D24 are 0.

## 15. Candidate R2 artifact identities

Filled after packaging (CANDIDATE_MANIFEST / ZIP SHA-256 / root).

## 16. Repository delta

New branch `cursor/ott-v056-cmcr2-d621`. Does not merge to `main`. Does not rewrite R1 evidence.

## 17. Deviations/incidents

None beyond the D21 STOP. GHCR pull of the accepted image is not required; the local accepted image was used for hash verification.

## 18. Scientific no-observation statement

```
SCIENTIFIC_OBSERVATIONS = 0
PUBLIC_V0_5_6_DOI = NOT RESERVED
PUBLICATION = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 19. Final strings

```
STOP_IPC_OFFICIAL_BENCHMARK_MANIFEST_MISMATCH
CAE_MAPPING = COMPLETE_AND_UNAMBIGUOUS
DECISIONS_IMPLEMENTED = 24/24
D21_IPC_OFFICIAL_MANIFEST = FAIL
V0.5.6_EXECUTION_SPEC_CANDIDATE_R2 = NOT READY_FOR_AUDIT
```

STOP.

## 20. REPORT IDENTITY

See OTT_REPORT_SIGNATURE in the accompanying message.
