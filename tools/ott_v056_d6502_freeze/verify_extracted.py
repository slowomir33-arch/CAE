#!/usr/bin/env python3
"""Verify extracted /ott-supplement files against the canonical Decoder6502 identity."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

CANONICAL_BYTES = 272629760
CANONICAL_SHA256 = "d231d459368c2049a73fd3b25377a657f08d4b95a7098112748b794abc673b62"
EXPECTED_FILES = [
    "Decoder6502.bin",
    "README.runtime-supplement.txt",
    "SUPPLEMENT_IDENTITY.json",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = Path(sys.argv[1])
    expected_content_root = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    bin_path = root / "Decoder6502.bin"
    man_path = root / "SUPPLEMENT_MANIFEST.sha256"
    ident_path = root / "SUPPLEMENT_IDENTITY.json"
    if not bin_path.is_file() or bin_path.stat().st_size != CANONICAL_BYTES:
        print("FAIL bytes", file=sys.stderr)
        return 2
    got = sha256_file(bin_path)
    if got != CANONICAL_SHA256:
        print(f"FAIL sha {got}", file=sys.stderr)
        return 2
    manifest = man_path.read_text(encoding="ascii")
    lines = [ln for ln in manifest.splitlines() if ln.strip()]
    if len(lines) != 3:
        print("FAIL manifest line count", file=sys.stderr)
        return 2
    seen = set()
    for ln in lines:
        digest, name = ln.split("  ", 1)
        seen.add(name)
        path = root / name
        if not path.is_file() or sha256_file(path) != digest:
            print(f"FAIL manifest {name}", file=sys.stderr)
            return 2
    if seen != set(EXPECTED_FILES):
        print(f"FAIL manifest names {seen}", file=sys.stderr)
        return 2
    content_root = hashlib.sha256(man_path.read_bytes()).hexdigest()
    if expected_content_root and content_root != expected_content_root:
        print(f"FAIL content_root {content_root} != {expected_content_root}", file=sys.stderr)
        return 2
    ident = json.loads(ident_path.read_text(encoding="utf-8"))
    if ident.get("asset_sha256") != CANONICAL_SHA256 or ident.get("asset_bytes") != CANONICAL_BYTES:
        print("FAIL identity", file=sys.stderr)
        return 2
    print(content_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
