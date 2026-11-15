from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import Swapp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-pid", type=int, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("idle-guard probing requires a new report path")
    result = {"authority": "native process enumeration and non-mutating idle guard", "started_at": time.time(), "expected_pid": args.expected_pid, "tool_hashes": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ("ProbeIdleGuard.py", "Swapp.py")}, "guard_refused": False, "limitation": "no COM activation, document APIs, dialog handling or cleanup commands are exercised"}

    def checkpoint(stage):
        result["stage"] = stage
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    try:
        result["before_pids"] = sorted(Swapp.application_pids())
        result["before_owned_pids"] = sorted(Swapp.owned_process_ids())
        checkpoint("before_guard")
        if args.expected_pid not in result["before_pids"] or result["before_owned_pids"]:
            raise RuntimeError("the selected unowned process is not available for an idle-guard observation")
        try:
            Swapp.sweep()
        except RuntimeError as error:
            result["guard_error"] = str(error)
            result["guard_refused"] = str(error).startswith("existing SOLIDWORKS processes prevent a fresh oracle session:")
        result["after_pids"] = sorted(Swapp.application_pids())
        result["after_owned_pids"] = sorted(Swapp.owned_process_ids())
        result["unchanged_process_set"] = result["after_pids"] == result["before_pids"]
        if not result["guard_refused"] or not result["unchanged_process_set"] or result["after_owned_pids"]:
            raise RuntimeError("the guarded refusal did not preserve the expected unowned process set")
        checkpoint("guard_observed")
    except Exception as error:
        result["exception"] = repr(error)
        result["failure_stage"] = result.get("stage", "initialization")
    result["finished_at"] = time.time()
    checkpoint("finished")
    return int(bool(result.get("exception")))


if __name__ == "__main__":
    raise SystemExit(main())
