"""D01/D02 canonical field framing and DOI-salted hashes."""
from __future__ import annotations

import hashlib
import re
import struct
import unicodedata
from typing import Iterable, Tuple, Union

from . import CAE_COMMIT, SENTINEL_DOI

TextLike = Union[str, int]
GIT_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class CanonicalError(ValueError):
    pass


def text_bytes(x: TextLike) -> bytes:
    if isinstance(x, bool) or x is None:
        raise CanonicalError(f"unsupported field type {type(x)}")
    if isinstance(x, int):
        if x < 0:
            raise CanonicalError("negative integers forbidden")
        s = str(x)
        if s != "0" and s.startswith("0"):
            raise CanonicalError("leading zeros forbidden")
        return s.encode("ascii")
    if not isinstance(x, str):
        raise CanonicalError(f"unsupported field type {type(x)}")
    if x.strip() != x:
        raise CanonicalError("surrounding whitespace forbidden; no silent trim")
    nfc = unicodedata.normalize("NFC", x)
    b = nfc.encode("utf-8")
    if b.startswith(b"\xef\xbb\xbf"):
        raise CanonicalError("UTF-8 BOM forbidden")
    return b


def field(x: TextLike) -> bytes:
    b = text_bytes(x)
    if len(b) > 0xFFFFFFFF:
        raise CanonicalError("field too long")
    return struct.pack(">I", len(b)) + b


def cat(*xs: TextLike) -> bytes:
    return b"".join(field(x) for x in xs)


def sha256_digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_cae_commit(commit: str) -> str:
    if not GIT_SHA40.fullmatch(commit):
        raise CanonicalError("CAE_commit must be lowercase 40-hex")
    if commit != CAE_COMMIT:
        raise CanonicalError("CAE_commit is not the runtime-executed pin")
    return commit


def require_doi(doi: str, *, allow_sentinel: bool) -> str:
    if doi.strip() != doi:
        raise CanonicalError("DOI surrounding whitespace forbidden")
    if not doi:
        raise CanonicalError("DOI empty")
    if doi == SENTINEL_DOI:
        if not allow_sentinel:
            raise CanonicalError("sentinel DOI forbidden in decisive mode")
        return doi
    if not allow_sentinel:
        # decisive mode still cannot run without later reservation; caller enforces
        return doi
    raise CanonicalError("tests must use the sentinel DOI")


def track_a_seed(
    doi: str,
    system: str,
    condition: str,
    replicate_index: int,
    cae_commit: str = CAE_COMMIT,
) -> Tuple[bytes, bytes]:
    require_cae_commit(cae_commit)
    if replicate_index < 0 or replicate_index > 31:
        raise CanonicalError("replicate_index must be 0..31")
    pre = cat(doi, cae_commit, system, condition, replicate_index)
    return sha256_digest(pre), pre


def track_b_split(doi: str, domain: str, canonical_relative_problem_path: str) -> Tuple[bytes, bytes]:
    pre = cat(doi, domain, canonical_relative_problem_path)
    return sha256_digest(pre), pre


def sort_by_raw_digest(items: Iterable[Tuple[bytes, bytes]]) -> list:
    """items: (digest32, tiebreak_utf8_path_bytes)."""
    return sorted(items, key=lambda t: (t[0], t[1]))
