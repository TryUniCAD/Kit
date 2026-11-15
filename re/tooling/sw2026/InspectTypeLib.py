from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pythoncom


def inspect(path, interface, method):
    if not path.is_absolute():
        raise ValueError("type-library inspection requires an absolute path")
    library = pythoncom.LoadTypeLib(str(path))
    methods = []
    for index in range(library.GetTypeInfoCount()):
        info = library.GetTypeInfo(index)
        if info.GetDocumentation(-1)[0] != interface:
            continue
        attributes = info.GetTypeAttr()
        for function_index in range(attributes.cFuncs):
            function = info.GetFuncDesc(function_index)
            names = info.GetNames(function.memid)
            if not names or names[0] != method:
                continue
            methods.append({
                "names": names,
                "member_id": function.memid,
                "invoke_kind": function.invkind,
                "arguments": repr(function.args),
                "return_type": repr(function.rettype),
            })
    if not methods:
        raise ValueError(f"{interface}.{method} is absent from the type library")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "library": repr(library.GetLibAttr()),
        "interface": interface,
        "method": method,
        "methods": methods,
        "scope": "Static installed type-library metadata; no CAD application launched or attached",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("interface")
    parser.add_argument("method")
    args = parser.parse_args()
    print(json.dumps(inspect(args.path, args.interface, args.method), indent=2))


if __name__ == "__main__":
    main()
