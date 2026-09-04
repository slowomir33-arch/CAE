"""D10 canonical POSIX relative paths."""
from __future__ import annotations

import unicodedata

from .canonical import CanonicalError, text_bytes


def canonical_relative_path(path: str) -> str:
    if path.strip() != path:
        raise CanonicalError("path surrounding whitespace forbidden")
    nfc = unicodedata.normalize("NFC", path)
    if nfc.startswith("/") or nfc.startswith("./"):
        raise CanonicalError("absolute or ./ paths forbidden")
    if "\\" in nfc:
        raise CanonicalError("backslash separators forbidden")
    parts = nfc.split("/")
    if any(p == "" for p in parts):
        raise CanonicalError("empty path segment forbidden")
    if any(p in (".", "..") for p in parts):
        raise CanonicalError(". or .. segments forbidden")
    # encode check
    text_bytes(nfc)
    return nfc
