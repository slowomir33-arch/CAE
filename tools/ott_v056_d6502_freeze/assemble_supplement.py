#!/usr/bin/env python3
"""Assemble the minimal Decoder6502 runtime-supplement build context on the GHA host."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

CANONICAL_BYTES = 272629760
CANONICAL_SHA256 = "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62"
RUNTIME_DIGEST = "sha256:1f9fad0bb1f8d65282ff237e0538e47a4e940e472fee7e915ec9c74fffe265b8"
CAE_COMMIT = "9164499c60ebe5ced32f0005009fc4e72aca77ca"
BREAK6502_COMMIT = "922af6496a2fa3b0a999e24419b5f8187f0ee98e"
LIBGATE_SHA256 = "ba8222d520c93ac8a3989857c8b2b3cb8573196ef185747eef60d8482dcf1964"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ctx = Path(sys.argv[1])
    bin_src = Path(sys.argv[2])
    readme_src = Path(sys.argv[3])
    freeze_id = os.environ["OTT_FREEZE_ID"]
    ctx.mkdir(parents=True, exist_ok=True)
    dst_bin = ctx / "Decoder6502.bin"
    shutil.copy2(bin_src, dst_bin)
    if dst_bin.stat().st_size != CANONICAL_BYTES or sha256_file(dst_bin) != CANONICAL_SHA256:
        print("STOP_D6502_SUPPLEMENT_REGENERATION_MISMATCH assemble copy", file=sys.stderr)
        return 2
    identity = {
        "document": "OTT_RUNTIME_SUPPLEMENT_IDENTITY",
        "protocol_version": "v0.5.6",
        "asset": "Decoder6502.bin",
        "asset_bytes": CANONICAL_BYTES,
        "asset_sha256": CANONICAL_SHA256,
        "base_runtime_digest": RUNTIME_DIGEST,
        "cae_commit": CAE_COMMIT,
        "break6502_commit": BREAK6502_COMMIT,
        "libgate6502_sha256": LIBGATE_SHA256,
        "generator": "libgate6502.so gate_init -> M6502Core::M6502(true,false) HLE",
        "scientific_semantics_delta": 0,
        "scientific_observations_before_freeze": 0,
        "freeze_run_id": freeze_id,
        "parent_diagnostic_run_id": "OTT-v0.5.6-D6502-20260904T112609Z-5B452FB6",
        "parent_github_run_id": "33867920935",
    }
    ident_path = ctx / "SUPPLEMENT_IDENTITY.json"
    ident_path.write_text(json.dumps(identity, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copy2(readme_src, ctx / "README.runtime-supplement.txt")
    names = ["Decoder6502.bin", "README.runtime-supplement.txt", "SUPPLEMENT_IDENTITY.json"]
    lines = []
    for name in names:
        digest = sha256_file(ctx / name)
        lines.append(f"{digest}  {name}")
    manifest = "\n".join(lines) + "\n"
    man_path = ctx / "SUPPLEMENT_MANIFEST.sha256"
    man_path.write_text(manifest, encoding="ascii")
    content_root = hashlib.sha256(man_path.read_bytes()).hexdigest()
    (ctx / "CONTENT_ROOT.txt").write_text(content_root + "\n", encoding="ascii")
    print(content_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
