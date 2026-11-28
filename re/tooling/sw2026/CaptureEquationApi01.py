from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "IModelDoc2": ("GetEquationMgr", "Parameter", "ForceRebuild3", "GetUpdateStamp"),
    "IEquationMgr": (
        "Add2",
        "GetCount",
        "Equation",
        "Value",
        "Status",
        "GlobalVariable",
        "EvaluateAll",
        "Disabled",
        "AutomaticSolveOrder",
        "AutomaticRebuild",
        "LinkToFile",
        "FilePath",
    ),
    "IDimension": (
        "FullName",
        "SystemValue",
        "SetSystemValue3",
        "DrivenState",
        "ReadOnly",
    ),
    "ISldWorks": ("GetUserPreferenceToggle", "SetUserPreferenceToggle"),
    "IModelDocExtension": ("GetWhatsWrongCount",),
}
ENUMS = {"swUserPreferenceToggle_e": ("swInputDimValOnCreate",)}
OPTIONAL = {
    "IEquationMgr": {
        "AutomaticSolveOrder",
        "AutomaticRebuild",
        "LinkToFile",
        "FilePath",
    }
}


def normalize(value):
    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    raise TypeError(
        "unsupported type-library descriptor value: " + type(value).__name__
    )


def capture():
    if os.name != "nt":
        raise ValueError(
            "the exact registered metadata must be captured inside the guest"
        )
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {
            key: pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
            for key, guid in LIBRARIES.items()
        }
        result = {
            "schema": "kit.sw2026.equation-api-metadata.v1",
            "native_processes_started": 0,
            "cad_documents_opened": 0,
            "preferences_read": 0,
            "preferences_written": 0,
            "interfaces": {},
            "enums": {},
            "libraries": {},
        }
        for key, library in libraries.items():
            attributes = library.GetLibAttr()
            if tuple(attributes[3:5]) != (34, 0):
                raise ValueError("a registered library does not match release 34.0")
            result["libraries"][key] = {
                "guid": str(attributes[0]),
                "lcid": attributes[1],
                "major": attributes[3],
                "minor": attributes[4],
            }
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attr = info.GetTypeAttr()
                if key == "sldworks" and name in MEMBERS:
                    rows = []
                    for ordinal in range(attr.cFuncs):
                        descriptor = info.GetFuncDesc(ordinal)
                        names = list(info.GetNames(descriptor.memid))
                        if names and names[0] in MEMBERS[name]:
                            rows.append(
                                {
                                    "names": names,
                                    "member_id": descriptor.memid,
                                    "invoke_kind": descriptor.invkind,
                                    "vtable_offset": descriptor.oVft,
                                    "arguments": normalize(descriptor.args),
                                    "return_type": normalize(descriptor.rettype),
                                    "optional_arguments": descriptor.cParamsOpt,
                                }
                            )
                    observed = {row["names"][0] for row in rows}
                    missing = set(MEMBERS[name]) - observed
                    result["interfaces"][name] = {
                        "guid": str(attr[0]),
                        "members": rows,
                        "missing_required": sorted(missing - OPTIONAL.get(name, set())),
                        "missing_optional": sorted(missing & OPTIONAL.get(name, set())),
                    }
                if key == "swconst" and name in ENUMS:
                    values = {}
                    for ordinal in range(attr.cVars):
                        descriptor = info.GetVarDesc(ordinal)
                        member = info.GetNames(descriptor.memid)[0]
                        if member in ENUMS[name]:
                            values[member] = normalize(descriptor.value)
                    result["enums"][name] = values
        missing_interfaces = sorted(set(MEMBERS) - set(result["interfaces"]))
        missing_enums = {
            name: sorted(set(members) - set(result["enums"].get(name, {})))
            for name, members in ENUMS.items()
        }
        result["missing_interfaces"] = missing_interfaces
        result["missing_enums"] = missing_enums
        result["passed"] = (
            not missing_interfaces
            and not any(
                row["missing_required"] for row in result["interfaces"].values()
            )
            and not any(missing_enums.values())
        )
        return result
    finally:
        pythoncom.CoUninitialize()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("the metadata output must be unused")
    result = capture()
    data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(data)
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "native_processes_started": 0,
            },
            sort_keys=True,
        )
    )
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
