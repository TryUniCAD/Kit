import argparse
from hashlib import sha256
from json import dumps
import os
from pathlib import Path


def capture(*, placement):
    if os.name != "nt":
        raise ValueError("registered annotation names are read on the root-owned oracle")
    import pythoncom

    pythoncom.CoInitialize()
    try:
        library = pythoncom.LoadRegTypeLib("{83A33D31-27C5-11CE-BFD4-00400513BB57}", 34, 0, 0)
        if tuple(library.GetLibAttr()[3:5]) != (34, 0):
            raise ValueError("expected the installed 2026 registered type library")
        requested = {
            "IAnnotation": {"GetPosition", "SetPosition2"},
            "INote": {"GetTextPoint", "GetTextPoint2"},
        } if placement else {"IAnnotation": {"GetName"}, "INote": {"GetName"}}
        interfaces = {}
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            name = info.GetDocumentation(-1)[0]
            if name not in requested:
                continue
            attrs = info.GetTypeAttr()
            for ordinal in range(attrs.cFuncs):
                desc = info.GetFuncDesc(ordinal)
                names = list(info.GetNames(desc.memid))
                if names and names[0] in requested[name]:
                    captured = interfaces.setdefault(name, {})
                    if names[0] in captured:
                        raise ValueError("ambiguous registered annotation accessor")
                    captured[names[0]] = {
                        "interface_guid": str(attrs[0]),
                        "member_id": desc.memid,
                        "invocation_kind": desc.invkind,
                        "arguments": repr(desc.args),
                        "return_type": repr(desc.rettype),
                        "vtable_offset": desc.oVft,
                    }
        if placement:
            if set(interfaces.get("IAnnotation", {})) != requested["IAnnotation"]:
                raise ValueError("missing expected actual annotation placement accessors")
            schema = "kit.sw2026.registered-annotation-placement-access.v1"
        else:
            if set(interfaces) != set(requested) or interfaces["IAnnotation"]["GetName"]["member_id"] != 21:
                raise ValueError("missing expected actual annotation name accessors")
            interfaces = {name: values["GetName"] for name, values in interfaces.items()}
            schema = "kit.sw2026.registered-annotation-name-access.v1"
        return {
            "schema": schema,
            "type_library_version": [34, 0],
            "native_processes_started": 0,
            "interfaces": interfaces,
            "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        }
    finally:
        pythoncom.CoUninitialize()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--placement", action="store_true")
    args = parser.parse_args()
    result = capture(placement=args.placement)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(dumps(result, sort_keys=True, indent=2) + "\n")
    print(dumps({"passed": True, "result_sha256": sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
