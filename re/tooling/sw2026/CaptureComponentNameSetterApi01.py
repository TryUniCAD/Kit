import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from CaptureComponentNameApi01 import capture as capture_base


def require(value, message):
    if not value:
        raise ValueError(message)


def capture():
    require(os.name == "nt", "only root reads the registered guest setter metadata")
    value = capture_base()
    require(
        value["passed"] is True and value["enums"]["swExtRefUpdateCompNames"] == 18,
        "exact component metadata prerequisite differs",
    )
    import pythoncom

    pythoncom.CoInitialize()
    try:
        library = pythoncom.LoadRegTypeLib(
            "{83A33D31-27C5-11CE-BFD4-00400513BB57}", 34, 0, 0
        )
        require(
            tuple(library.GetLibAttr()[3:5]) == (34, 0),
            "actual setter type library differs",
        )
        rows = []
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            if info.GetDocumentation(-1)[0] != "ISldWorks":
                continue
            attrs = info.GetTypeAttr()
            for ordinal in range(attrs.cFuncs):
                desc = info.GetFuncDesc(ordinal)
                names = list(info.GetNames(desc.memid))
                if names and names[0] == "SetUserPreferenceToggle":
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
        require(
            len(rows) == 1
            and rows[0]["invoke_kind"] == 1
            and len(rows[0]["names"]) == 3,
            "actual name-preference setter signature is missing or ambiguous",
        )
        value["interfaces"]["ISldWorks"]["members"].extend(rows)
        value["base_tool_sha256"] = value["tool_sha256"]
        value["tool_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
        value["schema"] = "kit.sw2026.component-name-setter-api-metadata.v1"
        return value
    finally:
        pythoncom.CoUninitialize()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "setter metadata output must be unused")
    value = capture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
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
