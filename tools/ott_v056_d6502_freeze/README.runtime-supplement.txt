OTT v0.5.6 Decoder6502 immutable runtime supplement

This OCI image is a minimal data supplement. It is not a replacement for
ghcr.io/slowomir33-arch/cae-ott-v055-runtime and it is not a scientific
observation.

Canonical payload:
  /ott-supplement/Decoder6502.bin
  bytes = 272629760
  SHA-256 = d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62

Generator (pinned parent runtime only):
  libgate6502.so gate_init -> M6502Core::M6502(true, false) HLE

See SUPPLEMENT_IDENTITY.json and SUPPLEMENT_MANIFEST.sha256.
Do not use this supplement for Stage A until a later RUN_AUTHORIZATION
supersession binds this digest to the base runtime.
