from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from win32api import GetFileVersionInfo, OpenProcess
from win32process import GetModuleFileNameEx

EXPECTED_VERSION = (34, 5, 2, 604)


def application_identity(application):
    member = application.GetProcessID
    process_id = int(member() if callable(member) else member)
    handle = OpenProcess(0x410, False, process_id)
    try:
        path = Path(GetModuleFileNameEx(handle, None))
    finally:
        handle.Close()
    data = path.read_bytes()
    information = GetFileVersionInfo(str(path), "\\")
    high, low = information["FileVersionMS"], information["FileVersionLS"]
    version = (high >> 16, high & 0xFFFF, low >> 16, low & 0xFFFF)
    if data[:2] != b"MZ" or len(data) < 64:
        raise RuntimeError("oracle process executable is not a PE image")
    offset = struct.unpack_from("<I", data, 60)[0]
    if offset + 6 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        raise RuntimeError("oracle process executable has no valid PE header")
    return {
        "process_id": process_id, "executable": path.name,
        "file_version": ".".join(str(value) for value in version[:3]) + f".{version[3]:04d}",
        "file_version_words": list(version), "expected_version": list(EXPECTED_VERSION),
        "version_matches": version == EXPECTED_VERSION,
        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        "pe_machine": hex(struct.unpack_from("<H", data, offset + 4)[0]),
    }


def active_identity():
    import argparse
    import json
    import pythoncom
    from win32com.client import DispatchEx, GetActiveObject

    parser = argparse.ArgumentParser()
    parser.add_argument("--existing-pid", type=int)
    args = parser.parse_args()

    def value(obj, name):
        member = getattr(obj, name)
        return member() if callable(member) and not hasattr(member, "_oleobj_") else member

    pythoncom.CoInitialize()
    try:
        if args.existing_pid is None:
            application = GetActiveObject("SldWorks.Application.34")
        else:
            from AuthorCurves import application_pids
            if args.existing_pid not in application_pids():
                raise RuntimeError("the explicitly selected preexisting process is absent")
            application = DispatchEx("SldWorks.Application.34")
        identity = application_identity(application)
        if args.existing_pid is not None and identity["process_id"] != args.existing_pid:
            raise RuntimeError("versioned COM activation did not return the explicitly selected existing process")
        identity["revision"] = str(value(application, "RevisionNumber"))
        identity["document_count"] = int(value(application, "GetDocumentCount"))
        identity["visible"] = bool(value(application, "Visible"))
        identity["user_control"] = bool(value(application, "UserControl"))
        documents = value(application, "GetDocuments") or []
        identity["documents"] = [
            {"title": str(value(document, "GetTitle")), "path": str(value(document, "GetPathName")), "dirty": bool(value(document, "GetSaveFlag"))}
            for document in documents
        ]
        identity["inspection_scope"] = "application identity and document metadata only; no properties written or documents opened, created, saved or closed"
        print(json.dumps(identity))
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    active_identity()
