from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os

GUIDS = (
    "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
)
APP_HASH = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TYPE_FILTERS = ("holewizard", "wizardhole", "simplehole", "advancedhole", "holeseries", "wzdhole", "wzdgeneralhole")


def identity():
    import winreg
    from win32api import GetFileVersionInfo

    sep = chr(92)
    clsid = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, sep.join(("SldWorks.Application.34", "CLSID")))
    path = Path(winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, sep.join(("CLSID", clsid, "LocalServer32"))).strip('"'))
    info = GetFileVersionInfo(str(path), sep)
    high, low = info["FileVersionMS"], info["FileVersionLS"]
    version = f"{high >> 16}.{high & 65535}.{low >> 16}.{low & 65535:04d}"
    digest = sha256(path.read_bytes()).hexdigest()
    if path.name.casefold() != "sldworks.exe" or digest != APP_HASH or version != "34.5.2.0604":
        raise ValueError("installed SOLIDWORKS executable differs")
    return {"file_version": version, "sha256": digest, "prog_id": "SldWorks.Application.34"}


def discover():
    import pythoncom

    libraries = [pythoncom.LoadRegTypeLib(guid, 34, 0, 0) for guid in GUIDS]
    if [tuple(value.GetLibAttr()[3:5]) for value in libraries] != [(34, 0), (34, 0)]:
        raise ValueError("registered model and enum metadata must use version 34.0")
    methods, enums = {}, {}
    for library in libraries:
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            name = info.GetDocumentation(-1)[0]
            attrs = info.GetTypeAttr()
            selected = any(key in name.casefold() for key in TYPE_FILTERS)
            if attrs.typekind == pythoncom.TKIND_ENUM and selected:
                values = {}
                for slot in range(attrs.cVars):
                    desc = info.GetVarDesc(slot)
                    enum = info.GetNames(desc.memid)[0]
                    if type(desc.value) is int:
                        values[enum] = desc.value
                if values:
                    enums[name] = values
            if attrs.typekind not in (pythoncom.TKIND_INTERFACE, pythoncom.TKIND_DISPATCH):
                continue
            if not selected and name != "IFeatureManager":
                continue
            for slot in range(attrs.cFuncs):
                desc = info.GetFuncDesc(slot)
                members = list(info.GetNames(desc.memid))
                if not members or (not selected and "hole" not in members[0].casefold()):
                    continue
                owner = methods.setdefault(name, {})
                key = (members[0], desc.invkind)
                if key in owner:
                    raise ValueError("duplicate native method and invocation kind")
                owner[key] = {"names": members, "member_id": desc.memid, "invocation_kind": desc.invkind,
                              "arguments": repr(desc.args), "return_type": repr(desc.rettype)}
    if not methods or not enums:
        raise ValueError("installed hole authoring declarations were not found")
    return {name: list(values.values()) for name, values in methods.items()}, enums


def capture():
    if os.name != "nt":
        raise ValueError("hole API metadata is captured only in the installed Windows oracle")
    import pythoncom

    actual = identity()
    pythoncom.CoInitialize()
    try:
        methods, enums = discover()
    finally:
        pythoncom.CoUninitialize()
    return {"schema": "kit.sw2026.hole-source-installation.v1", "executable": actual, "libraries": ["34.0", "34.0"],
              "methods": methods, "enums": enums, "native_processes": 0, "native_files_authored": 0, "heldout_sources": 0}


def encode(report):
    return (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = capture()
    body = encode(report)
    with args.output.open("xb") as stream:
        stream.write(body)
    print(json.dumps({"sha256": sha256(body).hexdigest(), "bytes": len(body),
                      "owners": {key: len(rows) for key, rows in report["methods"].items()},
                      "enums": {key: len(rows) for key, rows in report["enums"].items()}, "native_processes": 0}))


if __name__ == "__main__":
    main()
