---
document_type: OTT_v0.5.5_FINAL_FREEZE_REPORT
document_id: OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A-M007
run_id: OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A
created_at_utc: 2026-09-04T01:38:17Z
protocol_version: v0.5.5
stage: FINAL_FREEZE_RUNTIME_PERSISTENCE_EXECUTION
final_verdict: FINAL_FREEZE = PASS
---

OTT_REPORT_SIGNATURE
PROTOCOL_VERSION: v0.5.5
STAGE: FINAL_FREEZE_RUNTIME_PERSISTENCE_EXECUTION
RUN_ID: OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A
MESSAGE_ID: OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A-M007
REPORT_TYPE: FINAL_REPORT
CREATED_AT_UTC: 2026-09-04T01:38:17Z
AGENT: Cursor Agent (cursor-grok-4.6-high-fast) bc-a44d5fad-cc3c-4213-86ff-505b70bdd621
PARENT_RUN_ID: OTT-v0.5.5-DCBA-20260904T001221Z-6E4DAE55
INPUT_ZIP_SHA256: a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018
GHCR_PREFLIGHT_RUN_ID: 33820845747
GHCR_PREFLIGHT_CANARY_DIGEST: sha256:ddf31c99c732e96d0a037dd99c283b0e0ba45049e20261585185ec2c91548326
END_OTT_REPORT_SIGNATURE

# OTT v0.5.5 — FINAL FREEZE / IMMUTABLE RUNTIME CLOSURE REPORT

Header:
OTT v0.5.5 FINAL FREEZE CLOSED — IMMUTABLE RUNTIME PERSISTED — SCIENTIFIC CHALLENGE NOT RUN

## 1. Verdict

**FINAL_FREEZE = PASS**

```text
BUILD_RUNTIME_OK = PASS
APT_REPRODUCIBILITY_CLOSURE = PASS
PERSISTED_IMMUTABLE_RUNTIME = PASS
FINAL_FREEZE = PASS
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 2. Report identity

| Field | Value |
|---|---|
| RUN_ID | `OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A` |
| MESSAGE_ID | `OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A-M007` |
| PARENT_RUN_ID | `OTT-v0.5.5-DCBA-20260904T001221Z-6E4DAE55` |
| CREATED_AT_UTC | `2026-09-04T01:38:17Z` |
| PACKET.md SHA-256 | `c3ec0a31a916c63783f8fe0bbb5e75b9a3121cba3b89da78695013e336dc81e2` |
| AGENT | Cursor Agent bc-a44d5fad-cc3c-4213-86ff-505b70bdd621 |

## 3. Authoritative input / seal

| Field | Value |
|---|---|
| Filename | `OTT_External_Blind_Challenge_v0.5.5_PREFREEZE_EXECUTION_CLOSURE.zip` |
| ZIP SHA-256 | `a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018` |
| ZIP bytes | 47137 |
| PREFREEZE_ROOT_SHA256 | `db6e1d45946b02c2226eb2a08c1ac431dfe74ff1d5241eec52ecd6eb55b7692b` |
| MANIFEST | 27/27 |
| CONTRACT | 7/7 PASS |

## 4. Secure build-host ingress

- Category: private author-controlled local path on the Cursor execution host (ZIP downloaded by the author-supplied Drive artifact, hashed, then kept outside the public git repository).
- SHA-256 before ingress: `a1becacfa4b38104d4f7e47caf6f0a7e7da475152c0b5da3497b3a28d5451018`
- SHA-256 after local placement: identical
- ZIP was not committed to `slowomir33-arch/CAE`, not embedded in workflow YAML, not published as a release asset.

## 5. Build-host identity

```text
uname: Linux cursor 6.12.94+ x86_64
Docker Engine: 29.8.0 (containerd-snapshotter=false, storage-driver=vfs)
BuildKit: docker-buildx 0.37.0
Platform: linux/amd64
Build start: 2026-09-04T00:39:00Z
Build end:   2026-09-04T00:45:15Z
BUILD_EXIT=0
```

First BuildKit attempt failed on nested overlay (`invalid argument`). Host-only Docker reconfiguration to `vfs` (outside the sealed recipe) unblocked the build. Recipe bytes were not changed.

## 6. APT reproducibility closure

- Inherited `/etc/apt/sources.list.d/debian.sources` removed by the sealed Dockerfile.
- Only `snapshot.debian.org` @ `20250906T112439Z`.
- Build-log `Get:` lines: 84 total = 4 index files + **80 packages**, all `snapshot.debian.org`.
- NON_SNAPSHOT = 0
- AMBIGUOUS = 0
- LIVE `deb.debian.org` / `security.debian.org` fetches = 0
- Known base versions observed in install: `libc6 2.36-9+deb12u13`, `g++ 12.2.0-14+deb12u1`

```text
APT_REPRODUCIBILITY_CLOSURE = PASS
80/80 SNAPSHOT-RESOLVED
```

## 7. Source closure

All 8 git HEADs matched frozen pins:

```text
CAE            9164499c60ebe5ced32f0005009fc4e72aca77ca
tracr          9ce2b8c82b6ba10e62e86cf6f390e7536d4fd2cd
ipc2020-domains 9e313248244a0a13302ae262f42ef446f43e4182
lilotane       0a58c299c7d85034661f795dfe7b10ad64f547d3
pandaPIparser  95bbe291c5bdb9fb517c1ad55f5136d45450c644
fake6502       b52676f840983219b0b9baa13f1d0ebc07aac9f9
break6502      922af6496a2fa3b0a999e24419b5f8187f0ee98e
perfect6502    09fc542877a84318291aa42dab143a3e2c3db974
```

Glucose archive SHA-256 verified:
`51aa1cf1bed2b14f1543b099e85a56dd1a92be37e6e3eb0c4a1fd883d5cc5029`

Patches:
```text
ef46037f57eef6b84b0a2bdca42543f9961b627c420aabc8ba4d055ded6f1b52  Solver.h.patch
7cb1bbafd69ba83b305fd65e3514a02fe930022af48a5366a5e85f3fdb78597b  Solver.cc.patch
```

`setLearnCallback` evidence present. Lilotane flags exactly `-include limits -include optional` (no `cstddef`).

## 8. Runtime build

- Recipe: sealed `environment/Dockerfile.prefreeze` + `acquire_sources.sh` + `build_runtime.sh`
- `--no-cache --platform linux/amd64`
- Local image ID: `sha256:204e3b2dd396767d671e132de2ec76634886fd14f08b811d64c623659d353f86`
- Staging tag: `ghcr.io/slowomir33-arch/cae-ott-v055-runtime:freeze-OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A`

## 9. Test gates

| Gate | Result |
|---|---|
| IMPORTS | PASS |
| BRIDGES | 3/3 |
| Lilotane | 100% / bin OK |
| CAE (local image) | 111/111 PASS |
| CAE (retrieved image) | 111/111 PASS |
| OTT contract (fresh sealed extract) | 7/7 PASS |
| OTT contract (local image + mounted sealed tree) | 7/7 PASS |
| pip check | known `phrasedml 1.3.0 is not supported on this platform` |

## 10. Runtime fingerprint

```text
runtime_fingerprint.json SHA-256 = 8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd
runtime_fingerprint root         = 166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271
12/12 semantic fingerprint artifacts identical
```

Retrieved-image fingerprint matched the same two hashes exactly.

## 11. SBOM

- Generator: syft 1.51.1
- Format: CycloneDX JSON spec 1.7
- Component count: 12470
- SHA-256: `4d36b5d4daefb6ae5e811f5aef1bc59fc977252bb41b6d21d7c7dd016ce91d06`
- Historical reference: 431 components / `7717a1c68ba49c9713d1bc2a28bcb6724366d4719350e440a0c4c583f06bd87a`
- Interpretation: generator/cataloger scope difference (default syft file+package inventory vs historical package-closure SBOM). Not treated as a new runtime pin/source/base defect because application/runtime semantic fingerprint matched 12/12.

## 12. OCI identity

| Field | Value |
|---|---|
| Platform | linux/amd64 |
| Image ID / config digest | `sha256:204e3b2dd396767d671e132de2ec76634886fd14f08b811d64c623659d353f86` |
| Manifest digest | `sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8` |
| Compressed layer bytes | 7516999420 |
| Local vfs size | ~12.3 GB |
| Manifest media type | application/vnd.docker.distribution.manifest.v2+json |

Largest compressed layer: `sha256:20d2c1504fdf2a95ae6e92cdb5e9538fca10e7844afce1590e7f96b134bfa406` (7322977797 bytes).

## 13. GHCR publication

```text
GHCR_PUSH = PASS
IMMUTABLE_DIGEST = ESTABLISHED
PUSHED_IMMUTABLE_REF=ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
```

Push window: `2026-09-04T01:13:44Z` → `2026-09-04T01:27:25Z` (large layer retried once, then pushed).

Package currently **private** and not linked to the git repository in GHCR metadata. Independent retrieval used a repository Actions secret `GHCR_PULL_TOKEN` (not written into YAML). Revoke the chat PAT and delete that secret after auditor inspection.

## 14. Independent pull-by-digest

- Fresh GitHub-hosted runner (not the build Docker daemon)
- Run: https://github.com/slowomir33-arch/CAE/actions/runs/33826209738
- Job B ID: `100879309934`
- JOB_B_RUNNER=`GitHub Actions 1000001282 os=Linux arch=X64 ImageVersion=20260831.293.1`
- Event: `push` on `ott/v0.5.5-final-freeze` commit `f08c9a03fde219e55d9800574dcc039e499521c2`
- Pull: `ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8`

```text
PUSHED_DIGEST=sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
PULLED_DIGEST=sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
DIGEST_IDENTITY=EXACT_MATCH
```

## 15. Post-retrieval execution

On the image just pulled from GHCR (not the original local build container):

```text
IMPORTS=PASS
BRIDGES=3/3
LILOTANE_BIN=OK
FP_JSON_SHA256 8ab74b5d7bb737275daf9cb4fb13edfef21cacb9a5f3b6a20c5b0ad637a317dd
FP_ROOT 166068659b03c450b9ba2425f324bd4cfb2338a3784ee3c6fa764f0a8f256271
PIP_FREEZE_SHA256 0f9bfbf13cca0f5d58df1892c3c63e8834a592ebb74ecda2c5f08414bb77d147
RETRIEVED_RUNTIME_FINGERPRINT=accepted_v0.5.5_identity
CAE 111 passed in 4.85s
```

OTT contract 7/7 is a sealed-tree check (protocol file hashes). It was run on the fresh extraction and again inside the local image with the sealed tree mounted read-only. The retrieved GHCR image does not contain the sealed ZIP; in-image gates above are what the frozen image can execute.

```text
PERSISTED_IMMUTABLE_RUNTIME = PASS
```

## 16. Repository/infrastructure delta

This execution wrote only:

```text
.github/workflows/ott-v055-final-freeze.yml
```

on branch `ott/v0.5.5-final-freeze` (base `f8a8c10537b47b9fdc55cbc13a716de537b525af`).

Commits:
- `96a0434274188c2ffad6c651867d19a5d499f775` (initial workflow)
- `f08c9a03fde219e55d9800574dcc039e499521c2` (YAML fix)

`main` was not modified. No merge to `main`. Sealed ZIP was not committed. Scientific/runtime source files in CAE were not edited.

Prior preflight branch `ott/v0.5.5-ghcr-preflight` remains at `828a43a9c8e04d4bbcb1014165cb4aa9566ffd7b` from the parent execution.

## 17. Finalize-freeze receipts

Created **outside** the sealed tree and **not** added to `main`:

- `/opt/cursor/artifacts/FINALIZE_FREEZE.json`
- `/opt/cursor/artifacts/OTT_v0.5.5_FINAL_FREEZE_REPORT_20260904T013817Z_E0F1128A.md`

## 18. Deviations / incidents

1. Nested-overlay BuildKit failure on the Cursor VM; host Docker switched to `vfs` (not a recipe change).
2. Cursor installation token could not create the GHCR package; author PAT used only for `docker login`/`docker push` and to create repo secret `GHCR_PULL_TOKEN`. PAT must be revoked.
3. Large layer retried once during push, then succeeded.
4. First retrieval workflow YAML failed to parse (0s); fixed in `f08c9a0` and re-run.
5. SBOM component count differs from historical 431 due to syft default catalogers; semantic fingerprint matched.

No scientific-code repair. No `cstddef` flag. No pin changes.

## 19. Scientific invariance

```text
SCIENTIFIC_BYTES_CHANGED = NO
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 20. Evidence inventory

- Seal: ZIP hash, manifest 27/27, PREFREEZE root, contract 7/7
- Host check + docker-build.log
- Local fingerprint dir + runtime_fingerprint.json
- GHCR push log + imagetools/raw manifest
- Job B retrieval log (run 33826209738)
- FINALIZE_FREEZE.json + this report

## 21. Final strings

```text
BUILD_RUNTIME_OK = PASS
APT_REPRODUCIBILITY_CLOSURE = PASS
PERSISTED_IMMUTABLE_RUNTIME = PASS
FINAL_FREEZE = PASS
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

## 22. REPORT IDENTITY

- RUN_ID: `OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A`
- MESSAGE_ID: `OTT-v0.5.5-FFRPE-20260904T003448Z-E0F1128A-M007`
- CREATED_AT_UTC: `2026-09-04T01:38:17Z`
- PROTOCOL_VERSION: `v0.5.5`
- STAGE: `FINAL_FREEZE_RUNTIME_PERSISTENCE_EXECUTION`
- FINAL_VERDICT: `FINAL_FREEZE = PASS`

```text
STOP.
```
