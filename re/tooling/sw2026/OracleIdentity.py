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
    import json
    import pythoncom
    from win32com.client import GetActiveObject

    def value(obj, name):
        member = getattr(obj, name)
        return member() if callable(member) and not hasattr(member, "_oleobj_") else member

    pythoncom.CoInitialize()
    try:
        application = GetActiveObject("SldWorks.Application.34")
        identity = application_identity(application)
        identity["revision"] = str(value(application, "RevisionNumber"))
        documents = value(application, "GetDocuments") or []
        identity["documents"] = [
            {"title": str(value(document, "GetTitle")), "path": str(value(document, "GetPathName")), "dirty": bool(value(document, "GetSaveFlag"))}
            for document in documents
        ]
        print(json.dumps(identity))
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    active_identity()
