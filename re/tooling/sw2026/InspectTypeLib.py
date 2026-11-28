from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import sys

import pythoncom


def inspect(path, interface, method):
    if not path.is_absolute():
        raise ValueError("type-library inspection requires an absolute path")
    path = path.resolve(strict=True)
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    library = pythoncom.LoadTypeLib(str(path))
    library_attributes = library.GetLibAttr()
    types = []
    methods = []
    constants = []
    for index in range(library.GetTypeInfoCount()):
        info = library.GetTypeInfo(index)
        name = info.GetDocumentation(-1)[0]
        if not fnmatchcase(name, interface):
            continue
        attributes = info.GetTypeAttr()
        declaring_type = {
            "name": name,
            "guid": str(attributes[0]),
            "type_kind": attributes.typekind,
            "type_index": index,
        }
        types.append(declaring_type)
        for function_index in range(attributes.cFuncs):
            function = info.GetFuncDesc(function_index)
            names = info.GetNames(function.memid)
            if not names or not fnmatchcase(names[0], method):
                continue
            methods.append(
                {
                    "names": names,
                    "member_id": function.memid,
                    "invoke_kind": function.invkind,
                    "arguments": repr(function.args),
                    "return_type": repr(function.rettype),
                    "declaring_type": declaring_type,
                }
            )
        if attributes.typekind != pythoncom.TKIND_ENUM:
            continue
        for variable_index in range(attributes.cVars):
            variable = info.GetVarDesc(variable_index)
            names = info.GetNames(variable.memid)
            if not names or not fnmatchcase(names[0], method):
                continue
            if variable.varkind != pythoncom.VAR_CONST:
                raise ValueError(f"{name}.{names[0]} is not a constant")
            if type(variable.value) is not int:
                raise TypeError(f"{name}.{names[0]} has unsupported enum value type {type(variable.value).__name__}")
            constants.append(
                {
                    "names": names,
                    "member_id": variable.memid,
                    "value": variable.value,
                    "variable_kind": variable.varkind,
                    "variable_flags": variable.wVarFlags,
                    "declared_type": repr(variable.elemdescVar),
                    "declaring_type": declaring_type,
                }
            )
    if not types:
        raise ValueError(f"{interface} is absent from the type library")
    if not methods and not constants:
        raise ValueError(f"{interface}.{method} is absent from the type library")
    if hashlib.sha256(path.read_bytes()).hexdigest() != source_hash:
        raise ValueError("type-library file changed during inspection")
    tool_path = Path(__file__).resolve()
    return {
        "path": str(path),
        "sha256": source_hash,
        "library": repr(library_attributes),
        "library_identity": {
            "name": library.GetDocumentation(-1)[0],
            "guid": str(library_attributes[0]),
            "locale_id": library_attributes[1],
            "system_kind": library_attributes[2],
            "major_version": library_attributes[3],
            "minor_version": library_attributes[4],
            "flags": library_attributes[5],
        },
        "tool": {
            "path": str(tool_path),
            "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
            "python_version": sys.version,
        },
        "interface": interface,
        "method": method,
        "types": types,
        "methods": methods,
        "constants": constants,
        "scope": "Static installed type-library metadata; no CAD application launched or attached",
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect installed type-library declarations without CAD activation")
    parser.add_argument("path", type=Path)
    parser.add_argument("interface", help="case-sensitive declaring-type name pattern")
    parser.add_argument("method", help="case-sensitive method or enum-constant name pattern")
    args = parser.parse_args()
    print(json.dumps(inspect(args.path, args.interface, args.method), indent=2))


if __name__ == "__main__":
    main()
