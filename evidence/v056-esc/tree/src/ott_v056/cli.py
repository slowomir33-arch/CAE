"""Deterministic CLI. Stage A never invokes B–E."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import SENTINEL_DOI
from .stages import Harness, StageError, MAPPING_STOP


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ott-v056")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--doi", default=None)
    p.add_argument("--fixture", action="store_true", help="NON_SCIENTIFIC_TEST_FIXTURE only")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("precheck")
    sa = sub.add_parser("start-stage-a")
    sa.add_argument("--run-id", required=True)
    sa.add_argument("--utc", required=True)
    sa.add_argument("--protocol-root", required=True)
    sa.add_argument("--runtime-digest", required=True)
    sa.add_argument("--execution-spec-hash", required=True)
    sub.add_parser("stage-a-cae")
    ipc = sub.add_parser("stage-a-ipc-split")
    ipc.add_argument("--problems-json", type=Path, required=True)
    sub.add_parser("stage-a-ipc-baseline")
    sub.add_parser("stage-a-seal")
    sub.add_parser("stage-b-candidate-selection")
    sub.add_parser("stage-c-held-out")
    sub.add_parser("stage-d-score")
    sub.add_parser("stage-e-verdict")
    args = p.parse_args(argv)

    h = Harness(args.run_dir, fixture=args.fixture, doi=args.doi)
    try:
        if args.cmd == "precheck":
            print(json.dumps(h.precheck(), sort_keys=True))
        elif args.cmd == "start-stage-a":
            print(json.dumps(h.start_stage_a({
                "RUN_ID": args.run_id,
                "UTC": args.utc,
                "protocol_root": args.protocol_root,
                "runtime_digest": args.runtime_digest,
                "execution_spec_hash": args.execution_spec_hash,
            }), sort_keys=True, default=str))
        elif args.cmd == "stage-a-cae":
            if not args.fixture:
                print(MAPPING_STOP, file=sys.stderr)
                return 2
            systems = [
                ("logic_circuit", "valid"),
                ("logic_circuit", "fail"),
                ("logic_circuit", "inv_internal"),
                ("tracr", "valid"),
                ("tracr", "fail"),
                ("grn", "valid"),
                ("grn", "wrong_map"),
                ("grn", "wrong_high_level_model"),
                ("cpu_6502", "valid_gate_isa"),
                ("cpu_6502", "valid_transistor_gate"),
                ("cpu_6502", "valid_transistor_isa"),
                ("cpu_6502", "broken_gate_isa"),
                ("cpu_6502", "broken_transistor_gate"),
                ("cpu_6502", "broken_transistor_isa"),
            ]
            h.stage_a_cae(systems)
        elif args.cmd == "stage-a-ipc-split":
            problems = json.loads(args.problems_json.read_text())
            h.stage_a_ipc_split(problems)
        elif args.cmd == "stage-a-ipc-baseline":
            h.stage_a_ipc_baseline()
        elif args.cmd == "stage-a-seal":
            print(json.dumps(h.stage_a_seal(), sort_keys=True))
        elif args.cmd == "stage-b-candidate-selection":
            h.stage_b()
        elif args.cmd == "stage-c-held-out":
            h.stage_c()
        elif args.cmd == "stage-d-score":
            h.stage_d()
        elif args.cmd == "stage-e-verdict":
            h.stage_e()
        else:
            return 2
    except StageError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
