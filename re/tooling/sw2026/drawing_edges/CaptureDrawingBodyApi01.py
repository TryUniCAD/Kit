from hashlib import sha256
from inspect import signature
import json
from pathlib import Path
import pythoncom
from win32com.client import gencache

GUIDS = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "IEdge": ["GetBody"],
    "IPartDoc": ["GetBodies2"],
    "IBody2": ["GetEdges"],
    "IEntity": ["GetComponent"],
    "ISldWorks": ["IsSame"],
}
ENUMS = {"swBodyType_e": ["swSolidBody"], "swObjectEquality": None}


def normalized(value):
    if value is None or type(value) in [str, int, float, bool]:
        return value
    if type(value) in [tuple, list]:
        return [normalized(x) for x in value]
    return {"type": type(value).__name__}


def capture():
    pythoncom.CoInitialize()
    try:
        wrapper = gencache.GetModuleForTypelib(
            pythoncom.MakeIID(GUIDS["sldworks"]), 0, 34, 0
        )
        wrapper_hash = sha256(Path(wrapper.__file__).read_bytes()).hexdigest()
        if (
            wrapper_hash
            != "d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959"
        ):
            raise ValueError("registered 2026 wrapper differs")
        result = {
            "schema": 1,
            "wrapper_sha256": wrapper_hash,
            "interfaces": {},
            "enums": {},
            "libraries": {},
            "cad_objects_created": 0,
            "native_processes_started_by_tool": 0,
            "model_documents_opened": 0,
        }
        for kind, guid in GUIDS.items():
            library = pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
            attributes = library.GetLibAttr()
            if str(attributes[0]).lower() != guid.lower() or tuple(attributes[3:5]) != (
                34,
                0,
            ):
                raise ValueError("registered type library differs")
            result["libraries"][kind] = {
                "guid": str(attributes[0]),
                "major": attributes[3],
                "minor": attributes[4],
                "locale": attributes[1],
            }
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attributes = info.GetTypeAttr()
                if kind == "swconst" and name in ENUMS:
                    values = {}
                    for ordinal in range(attributes.cVars):
                        descriptor = info.GetVarDesc(ordinal)
                        member = info.GetNames(descriptor.memid)[0]
                        if ENUMS[name] is None or member in ENUMS[name]:
                            values[member] = descriptor.value
                    result["enums"][name] = values
                if kind != "sldworks" or name not in MEMBERS:
                    continue
                rows = []
                owner = getattr(wrapper, name, None)
                for ordinal in range(attributes.cFuncs):
                    descriptor = info.GetFuncDesc(ordinal)
                    names = list(info.GetNames(descriptor.memid))
                    if not names or names[0] not in MEMBERS[name]:
                        continue
                    row = {
                        "names": names,
                        "member_id": descriptor.memid,
                        "invoke_kind": descriptor.invkind,
                        "arguments": normalized(descriptor.args),
                        "return_type": normalized(descriptor.rettype),
                        "vtable_offset_bytes": descriptor.oVft,
                        "function_ordinal": ordinal,
                    }
                    function = (
                        getattr(owner, names[0], None) if owner is not None else None
                    )
                    if function is not None:
                        try:
                            shape = signature(function)
                            row["wrapper_parameters"] = [
                                {
                                    "name": item.name,
                                    "kind": str(item.kind),
                                    "has_default": item.default is not item.empty,
                                    "default": (
                                        normalized(item.default)
                                        if item.default is not item.empty
                                        else None
                                    ),
                                }
                                for item in shape.parameters.values()
                            ]
                        except (ValueError, TypeError):
                            row["wrapper_parameters"] = None
                    row["wrapper_has_property_get"] = bool(
                        owner is not None
                        and names[0] in getattr(owner, "_prop_map_get_", {})
                    )
                    row["wrapper_has_property_put"] = bool(
                        owner is not None
                        and names[0] in getattr(owner, "_prop_map_put_", {})
                    )
                    rows.append(row)
                result["interfaces"][name] = {
                    "guid": str(attributes[0]),
                    "members": rows,
                    "missing": [
                        value
                        for value in MEMBERS[name]
                        if not any(row["names"][0] == value for row in rows)
                    ],
                }
        result["tool_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
        return result
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    print(json.dumps(capture(), sort_keys=True, indent=2))
