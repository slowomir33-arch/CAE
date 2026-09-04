# OTT v0.5.6 — P2A PREPUBLICATION SECURITY RELOCK REPORT

## 1. Verdict

```
STOP_P2A_SECURITY_RELOCK_NOT_ESTABLISHED
SECURITY_CLEANUP_REQUIRES_AUTHOR_ACTION
PARENT_P1_IDENTITY = PASS
P1_LOCAL_TREE_LOCK = PASS
AUTHOR_PUBLISH_WINDOW = CLOSED
ZENODO_PUBLICATION = NO
SCIENTIFIC_OBSERVATIONS = 0
SCIENTIFIC_CHALLENGE_RUN = NO
RUN_AUTHORIZATION = NOT ISSUED
```

The new secret name is correct. It is **not** present in this already-running VM. P2A did not call Zenodo. The old credential was not used.

## 2. Parent P1 identity

Local re-read of PR #8 / commit `57c7b561bba4cb1fa8ab0c1e6db037658025f7be`:

```
ZIP bytes = 58243
ZIP SHA-256 = 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
CANDIDATE_ROOT = b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
DOI = 10.5281/zenodo.22293061
DEPOSITION = 22293061
```

`PARENT_P1_IDENTITY = PASS`

## 3. Security relock

Author stated: previous token revoked; new token added to settings as `ZENODO_P2A_WRITE_TOKEN`.

Observed in this VM:

```
ZENODO_P2A_WRITE_TOKEN in os.environ = NO
ZENODO_P2A_WRITE_TOKEN in any /proc/*/environ = NO
ZENODO_TOKEN in os.environ = NO
token recovered from chat/transcript/history = NO
old credential used = NO
deposit:actions used = NO
actions/publish called = NO
```

The leftover P1 ephemeral token file was overwritten with zeros and deleted. It was not used.

Independent proof that the old Zenodo token is dead was **not** obtained, because checking it would require using the old credential. Author declaration is recorded as `AUTHOR_DECLARED_REVOKED`, not as an API-proven revocation.

Cursor injects dashboard secrets at agent start. Adding a secret to settings during a live run does not update this VM.

## 4. Draft file / metadata re-read

Not performed. Authenticated Zenodo access requires the injected `ZENODO_P2A_WRITE_TOKEN`.

## 5. P1 scientific lock (local evidence only)

```
CAE mapping hash = 48b3fa3059e55cde2794209db62cd00a348cc04200253525e084fff023506d52
IPC = 30 / 20 / 40 / 30 = 120
runtime = ghcr.io/slowomir33-arch/cae-ott-v055-runtime@sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8
RUN_AUTHORIZATION.json = ABSENT
REAL_DOI_DERIVED_SCIENTIFIC_SEEDS = 0
REAL_DOI_DERIVED_IPC_SPLIT = 0
```

No P2A byte mutation.

## 6. Author action required

Do **not** paste the token into chat.

1. Keep the secret named exactly `ZENODO_P2A_WRITE_TOKEN`.
2. Scope: `deposit:write` only. Not `deposit:actions`.
3. Bind it to this Cloud Agent environment (the one used by this run).
4. **Start a new Cloud Agent** (or restart this one) so the secret is injected into `os.environ`.
5. Re-issue the same P2A packet. Do not publish.

Until that injection is visible in the new runtime, `AUTHOR_PUBLISH_WINDOW` stays closed.

## 7. Publication

```
ZENODO_PUBLICATION = NO
AUTHOR_PUBLISH_WINDOW = CLOSED
```

Do not click Publish.

## 8. Repository

Branch `cursor/ott-v056-p2a-stop-d621`. Do not merge to `main`. PR #8 remains the P1 candidate.

## 9. Final strings

```
STOP_P2A_SECURITY_RELOCK_NOT_ESTABLISHED
SECURITY_CLEANUP_REQUIRES_AUTHOR_ACTION
AUTHOR_PUBLISH_WINDOW = CLOSED
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
RUN_ID: OTT-v0.5.6-P2A-20260904T050425Z-392795B8
MESSAGE_ID: OTT-v0.5.6-P2A-20260904T050425Z-392795B8-M001
REPORT_TYPE: STOP_REPORT
CREATED_AT_UTC: 2026-09-04T05:04:25Z
AGENT: Cursor Agent cursor-grok-4.6
PARENT_P1_RUN_ID: OTT-v0.5.6-DOI-P1-20260904T043759Z-74EB9712
PARENT_P1_COMMIT: 57c7b561bba4cb1fa8ab0c1e6db037658025f7be
PARENT_P1_ZIP_SHA256: 41d5f23edd5d3fb44b6df8a746c4432ea09c781bc080855dd2949f993331314f
PARENT_P1_ROOT: b699fea96417a244f7276575f91f0bddd3c7e4f965a84ef167ef077a9ef0d516
ZENODO_DEPOSITION_ID: 22293061
PUBLIC_V0_5_6_DOI: 10.5281/zenodo.22293061
END_OTT_REPORT_SIGNATURE
```
