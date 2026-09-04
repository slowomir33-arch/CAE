"""D15/D17 output schema helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping

from . import NON_SCIENTIFIC


class OutputError(RuntimeError):
    pass


def dumps_scientific(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_empty_run_dir(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise OutputError(f"run path exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise OutputError("existing non-empty run directory; hard refusal (D17)")
    else:
        path.mkdir(parents=True)


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise OutputError(f"refusing overwrite of {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def jsonl_line(record: Dict[str, Any], *, fixture: bool) -> str:
    if fixture:
        record = dict(record)
        record[NON_SCIENTIFIC] = "YES"
    return dumps_scientific(record) + "\n"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
