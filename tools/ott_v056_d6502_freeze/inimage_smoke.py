#!/usr/bin/env python3
"""Fixed non-scientific GateSimulator NOP smoke. Requires CPU6502_LIB_DIR."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

RECEIPTS = Path(os.environ.get("OTT_RECEIPTS_DIR", "/ott/receipts"))
OUT_NAME = os.environ.get("OTT_SMOKE_OUT", "GATESIMULATOR_SMOKE.json")


def load_cpu():
    for cand in (
        Path("/opt/ott/sources/CAE/systems/10_cpu_6502.py"),
        Path("/workspace/systems/10_cpu_6502.py"),
    ):
        if cand.is_file():
            root = cand.parent.parent
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            spec = importlib.util.spec_from_file_location("cpu_6502_d6502f_smoke", str(cand))
            if spec is None or spec.loader is None:
                raise RuntimeError(f"cannot load {cand}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RuntimeError("10_cpu_6502.py not found")


def main() -> int:
    lib_dir = os.environ.get("CPU6502_LIB_DIR")
    if not lib_dir:
        raise SystemExit("CPU6502_LIB_DIR required")
    os.environ["CPU6502_LIB_DIR"] = lib_dir
    cpu = load_cpu()
    t0 = time.monotonic()
    sim = cpu.GateSimulator()
    ao, xo, yo, so, po = sim._exec(0xEA, 0, 1, 0, 0, 0, 0, 0)
    rec = {
        "CPU6502_LIB_DIR": lib_dir,
        "gate_init": "PASS",
        "sentinel": {
            "opcode": 0xEA,
            "operand": 0,
            "ilen": 1,
            "A_in": 0,
            "X_in": 0,
            "Y_in": 0,
            "S_in": 0,
            "P_in": 0,
        },
        "outputs": {"A_out": ao, "X_out": xo, "Y_out": yo, "S_out": so, "P_out": po},
        "wall_s": time.monotonic() - t0,
        "scientific": False,
        "PASS": True,
    }
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / OUT_NAME).write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SMOKE_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
