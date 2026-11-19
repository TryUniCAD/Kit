import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "ISldWorks": ("GetUserPreferenceToggle",),
    "IComponent2": ("Name2", "Select4", "GetID", "GetPathName"),
    "IFeature": ("Name", "GetID", "GetSpecificFeature2"),
    "ISelectionMgr": (
        "GetSelectedObjectCount2",
        "GetSelectedObject6",
        "GetSelectedObjectsComponent4",
    ),
    "IModelDoc2": ("ClearSelection2", "SelectionManager", "FirstFeature"),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def capture():
    require(
        os.name == "nt", "only the root-owned guest reads the registered type libraries"
    )
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {
            name: pythoncom.LoadRegTypeLib(value, 34, 0, 0)
            for name, value in LIBRARIES.items()
        }
        require(
            all(
                tuple(value.GetLibAttr()[3:5]) == (34, 0)
                for value in libraries.values()
            ),
            "expected both actual 2026 type libraries",
        )
        interfaces = {}
        enums = {}
        for library_name, library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attributes = info.GetTypeAttr()
                if library_name == "sldworks" and name in MEMBERS:
                    rows = []
                    for ordinal in range(attributes.cFuncs):
                        desc = info.GetFuncDesc(ordinal)
                        names = list(info.GetNames(desc.memid))
                        if names and names[0] in MEMBERS[name]:
                            rows.append(
                                {
                                    "names": names,
                                    "member_id": desc.memid,
                                    "invoke_kind": desc.invkind,
                                    "arguments": repr(desc.args),
                                    "return_type": repr(desc.rettype),
                                    "vtable_offset": desc.oVft,
                                }
                            )
                    interfaces[name] = {"guid": str(attributes[0]), "members": rows}
                if library_name == "swconst" and name == "swUserPreferenceToggle_e":
                    for ordinal in range(attributes.cVars):
                        desc = info.GetVarDesc(ordinal)
                        member = info.GetNames(desc.memid)[0]
                        if member == "swExtRefUpdateCompNames":
                            enums[member] = desc.value
        for interface, names in MEMBERS.items():
            require(
                interface in interfaces
                and all(
                    any(
                        row["names"][0] == name
                        for row in interfaces[interface]["members"]
                    )
                    for name in names
                ),
                "registered rename prerequisite missing in " + interface,
            )
        names = [
            row
            for row in interfaces["IComponent2"]["members"]
            if row["names"][0] == "Name2"
        ]
        require(
            len(names) == 2
            and {row["invoke_kind"] for row in names} == {2, 4}
            and {row["member_id"] for row in names} == {59},
            "actual component Name2 getter/setter differs",
        )
        require(
            set(enums) == {"swExtRefUpdateCompNames"}
            and type(enums["swExtRefUpdateCompNames"]) is int,
            "actual external-name preference enum is missing",
        )
        return {
            "schema": "kit.sw2026.component-name-api-metadata.v1",
            "interfaces": interfaces,
            "enums": enums,
            "libraries": {
                name: {
                    "guid": str(value.GetLibAttr()[0]),
                    "major": value.GetLibAttr()[3],
                    "minor": value.GetLibAttr()[4],
                }
                for name, value in libraries.items()
            },
            "passed": True,
            "native_processes_started": 0,
            "global_preference_changes": 0,
            "heldout_inputs_read": 0,
            "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        }
    finally:
        pythoncom.CoUninitialize()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "metadata output must be unused")
    result = capture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "passed": True,
                "output_sha256": sha256(args.output.read_bytes()).hexdigest(),
                "native_processes_started": 0,
                "global_preference_changes": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
