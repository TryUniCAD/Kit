from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pythoncom
import win32com.client as wc

from OracleIdentity import EXPECTED_VERSION, application_identity
import Swapp


class Probe:
    def __init__(self, output, expected_pid, expected_sha256):
        self.output = output
        tool = Path(__file__).resolve()
        self.data = {
            "scope": "Existing-session identity and document metadata only; no native acceptance",
            "progid": Swapp.PROGID,
            "expected_pid": expected_pid,
            "expected_sha256": expected_sha256,
            "expected_version": list(EXPECTED_VERSION),
            "tool_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
            "sidecar_sha256": {
                name: hashlib.sha256((tool.parent / name).read_bytes()).hexdigest()
                for name in ("Swapp.py", "OracleIdentity.py")
            },
            "snapshots": [],
            "failures": [],
            "healthy": False,
            "completed": False,
        }

    def checkpoint(self, stage):
        self.data["stage"] = stage
        self.data["updated_utc"] = datetime.now(timezone.utc).isoformat()
        self.output.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def call(self, stage, function, *args):
        self.checkpoint(stage + ":before")
        value = function(*args)
        self.checkpoint(stage + ":returned")
        return value


def require_identity(identity, expected_pid, expected_sha256):
    if identity["process_id"] != expected_pid:
        raise RuntimeError("active object PID does not match the explicitly selected process")
    if identity["executable"].casefold() != "sldworks.exe":
        raise RuntimeError("active object executable is not SLDWORKS.exe")
    if not identity["version_matches"] or identity["file_version_words"] != list(EXPECTED_VERSION):
        raise RuntimeError("active object executable version does not match the pinned oracle")
    if identity["sha256"] != expected_sha256:
        raise RuntimeError("active object executable hash does not match the requested oracle")


def document_snapshot(application, probe, index):
    snapshot = {"documents": [], "complete": False}
    probe.data["snapshots"].append(snapshot)
    stage = f"snapshot_{index}"
    before = probe.call(stage + ":count_before", Swapp.invoke, application, "GetDocumentCount")
    if type(before) is not int or before < 0:
        raise RuntimeError("GetDocumentCount returned an unsupported count")
    snapshot["count_before"] = before
    documents = probe.call(stage + ":documents", Swapp.invoke, application, "GetDocuments")
    if documents is None:
        documents = ()
    if not isinstance(documents, (tuple, list)) or len(documents) != before:
        raise RuntimeError("GetDocuments and GetDocumentCount disagree")
    for position, document in enumerate(documents):
        if document is None or not hasattr(document, "_oleobj_"):
            raise RuntimeError("GetDocuments returned a non-dispatch document")
        row = {}
        snapshot["documents"].append(row)
        for key, member in (("title", "GetTitle"), ("path", "GetPathName"), ("dirty", "GetSaveFlag")):
            value = probe.call(f"{stage}:document_{position}:{member}", Swapp.invoke, document, member)
            if key == "dirty":
                if type(value) not in (bool, int) or value not in (-1, 0, 1):
                    raise RuntimeError("GetSaveFlag returned an unsupported Boolean")
                value = bool(value)
            elif not isinstance(value, str):
                raise RuntimeError(f"{member} returned an unsupported string")
            row[key] = value
    after = probe.call(stage + ":count_after", Swapp.invoke, application, "GetDocumentCount")
    snapshot["count_after"] = after
    if type(after) is not int or after != before:
        raise RuntimeError("document count changed during inventory")
    snapshot["complete"] = True
    return sorted((row["title"], row["path"], row["dirty"]) for row in snapshot["documents"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-pid", required=True, type=int)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    expected_hash = args.expected_sha256.lower()
    if args.expected_pid <= 0:
        parser.error("--expected-pid must be positive")
    if len(expected_hash) != 64 or any(character not in "0123456789abcdef" for character in expected_hash):
        parser.error("--expected-sha256 must contain 64 hexadecimal characters")
    if not args.output.is_absolute():
        parser.error("--output must be an absolute unused file path")
    with args.output.open("x", encoding="utf-8"):
        pass
    probe = Probe(args.output, args.expected_pid, expected_hash)
    application = None
    initialized = False
    try:
        probe.data["application_pids_before"] = sorted(probe.call("application_pids_before", Swapp.application_pids))
        if args.expected_pid not in probe.data["application_pids_before"]:
            raise RuntimeError("the explicitly selected existing process is absent")
        probe.call("com_initialize", pythoncom.CoInitialize)
        initialized = True
        application = probe.call("get_active_object", wc.GetActiveObject, Swapp.PROGID)
        if application is None or not hasattr(application, "_oleobj_"):
            raise RuntimeError("GetActiveObject returned no existing dispatch object")
        pid = probe.call("active_process_id", Swapp.invoke, application, "GetProcessID")
        probe.data["active_process_id"] = pid
        if type(pid) is not int or pid != args.expected_pid:
            raise RuntimeError("active object returned the wrong process; no document query was issued")
        identity = probe.call("native_identity_before", application_identity, application)
        probe.data["native_identity_before"] = identity
        require_identity(identity, args.expected_pid, expected_hash)
        first = document_snapshot(application, probe, 1)
        second = document_snapshot(application, probe, 2)
        probe.data["documents_stable"] = first == second
        if first != second:
            raise RuntimeError("document title/path/dirty inventory changed between snapshots")
        final_identity = probe.call("native_identity_after", application_identity, application)
        probe.data["native_identity_after"] = final_identity
        require_identity(final_identity, args.expected_pid, expected_hash)
        probe.data["native_identity_stable"] = identity == final_identity
        if identity != final_identity:
            raise RuntimeError("native identity, including process creation time, changed")
        probe.checkpoint("release_com_references:before")
    except Exception as error:
        probe.data["failures"].append({"stage": probe.data.get("stage"), "error": repr(error)})
        probe.checkpoint("release_com_references:before")
    finally:
        application = None
        if initialized:
            pythoncom.CoUninitialize()
    try:
        probe.data["application_pids_after"] = sorted(probe.call("application_pids_after", Swapp.application_pids))
        probe.data["application_pids_stable"] = probe.data["application_pids_before"] == probe.data["application_pids_after"]
        if not probe.data["application_pids_stable"]:
            raise RuntimeError("application process inventory changed during inspection")
    except Exception as error:
        probe.data["failures"].append({"stage": probe.data.get("stage"), "error": repr(error)})
    probe.data["healthy"] = not probe.data["failures"]
    probe.data["completed"] = True
    probe.checkpoint("complete" if probe.data["healthy"] else "failed")
    print(json.dumps(probe.data))
    return 0 if probe.data["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
