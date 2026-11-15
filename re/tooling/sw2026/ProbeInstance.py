from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import Swapp
from AuthorCurves import application_pids, wait_exit
from OracleIdentity import application_identity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("instance probing requires a new report path")
    result = {"authority": "versioned COM activation and process identity only", "started_at": time.time(), "progid": Swapp.PROGID, "before_pids": sorted(application_pids()), "stage": "starting", "fresh_process": None, "existing_application_modified": False, "documents_created_or_opened": False, "cleanup_errors": []}

    def checkpoint(stage):
        result["stage"] = stage
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    application, owned_pid = None, None
    Swapp.pythoncom.CoInitialize()
    try:
        checkpoint("dispatch_start")
        application = Swapp.wc.DispatchEx(Swapp.PROGID)
        checkpoint("dispatch_return")
        identity = application_identity(application)
        result["identity"] = identity
        process_id = identity["process_id"]
        result["fresh_process"] = process_id not in result["before_pids"]
        checkpoint("identity_return")
        if result["fresh_process"]:
            owned_pid = process_id
            if not identity["version_matches"] or identity["sha256"] != "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe" or identity["pe_machine"] != "0x8664":
                raise RuntimeError("fresh COM process does not match the pinned 2026 oracle")
        else:
            result["limitation"] = "activation returned a preexisting process; no application properties, document calls or exit command were applied"
        checkpoint("probe_complete")
    except Exception as error:
        result["exception"] = repr(error)
        result["failure_stage"] = result["stage"]
    finally:
        if application is not None and owned_pid is not None:
            try:
                checkpoint("owned_exit_start")
                Swapp.invoke(application, "ExitApp")
                checkpoint("owned_exit_return")
            except Exception as error:
                result["cleanup_errors"].append(repr(error))
        application = None
        Swapp.pythoncom.CoUninitialize()
        if owned_pid is not None:
            result["owned_exit_confirmed"] = wait_exit(owned_pid)
            if not result["owned_exit_confirmed"]:
                result["cleanup_errors"].append("fresh owned process did not exit")
        result["after_pids"] = sorted(application_pids())
        result["preexisting_pids_missing_after"] = sorted(set(result["before_pids"]) - set(result["after_pids"]))
        result["finished_at"] = time.time()
        checkpoint("finished")
    return int(bool(result.get("exception") or result["cleanup_errors"] or not result["fresh_process"]))


if __name__ == "__main__":
    raise SystemExit(main())
