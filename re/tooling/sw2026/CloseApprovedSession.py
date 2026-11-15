from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import Swapp
from OracleIdentity import application_identity, process_creation_time
from win32api import OpenProcess
from win32event import WAIT_OBJECT_0, WaitForSingleObject


def main():
    parser = argparse.ArgumentParser(description="Close one explicitly authorized, clean existing oracle session")
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-pid", type=int, required=True)
    parser.add_argument("--expected-creation-filetime", type=int, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("existing handoff evidence must not be overwritten")
    result = {"started_at": time.time(), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "expected_pid": args.expected_pid, "expected_creation_filetime": args.expected_creation_filetime, "exit_requested": False, "exit_confirmed": False}
    application, documents, handle = None, None, None
    Swapp.pythoncom.CoInitialize()
    try:
        if Swapp.application_pids() != {args.expected_pid}:
            raise RuntimeError("the exact selected single existing session is unavailable")
        handle = OpenProcess(0x00100410, False, args.expected_pid)
        if process_creation_time(handle) != args.expected_creation_filetime:
            raise RuntimeError("the selected process lifetime changed before activation")
        application = Swapp.wc.GetActiveObject(Swapp.PROGID)
        identity = application_identity(application)
        result["identity"] = identity
        if identity["process_id"] != args.expected_pid or identity["process_creation_filetime"] != args.expected_creation_filetime:
            raise RuntimeError("the active object belongs to a different session")
        if not identity["version_matches"] or identity["sha256"] != "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe":
            raise RuntimeError("the selected oracle build or executable changed")
        documents = Swapp.cv(application, "GetDocuments") or []
        result["documents"] = [{"title": str(Swapp.cv(document, "GetTitle")), "path": str(Swapp.cv(document, "GetPathName")), "dirty": bool(Swapp.cv(document, "GetSaveFlag"))} for document in documents]
        if len(documents) != int(Swapp.cv(application, "GetDocumentCount")):
            raise RuntimeError("the open document inventory changed")
        if any(item["dirty"] or not item["path"] or not Path(item["path"]).is_file() for item in result["documents"]):
            raise RuntimeError("an unsaved, dirty or unavailable document prevents clean handoff")
        if any(bool(Swapp.cv(document, "GetSaveFlag")) for document in documents):
            raise RuntimeError("a document changed before the exit request")
        result["exit_requested"] = True
        Swapp.cv(application, "ExitApp")
        documents, application = None, None
        result["exit_confirmed"] = WaitForSingleObject(handle, 30000) == WAIT_OBJECT_0
        if not result["exit_confirmed"]:
            raise RuntimeError("the selected session did not exit; no forced termination was attempted")
    except Exception as error:
        result["error"] = repr(error)
    finally:
        documents, application = None, None
        if handle is not None:
            handle.Close()
        Swapp.pythoncom.CoUninitialize()
        result["finished_at"] = time.time()
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["exit_confirmed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
