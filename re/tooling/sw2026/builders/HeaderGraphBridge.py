from __future__ import annotations

from Core import Obj
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields, KExtTailFields, KHeaderFields, KLogFields, KRefCfgFields, KSharedFields, KStampFields,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def generated_header_bytes(root: Obj, version: int) -> bytes:
    converted: dict[int, ArchiveNode] = {}

    def wire_text(value):
        if not isinstance(value, str):
            raise ValueError("generated header strings require authored text")
        return CStringValue(value, True)

    def fields(source, layout):
        result = {}
        for name, kind in layout:
            if kind == "bounds":
                present = source["bboxflag"]
                if present not in (0, 1):
                    raise ValueError("generated header has an invalid bounds flag")
                result[name] = tuple(source[name][f"b{index}"] for index in range(10)) if present else None
            else:
                value = source[name]
                result[name] = wire_text(value) if kind == "text" else node(value) if isinstance(value, Obj) else value
        return result

    def node(source):
        if source is None:
            return None
        if not isinstance(source, Obj):
            raise ValueError("generated header requires a native model object")
        key = id(source)
        if key in converted:
            return converted[key]
        name = source.cls
        target = ArchiveNode(RuntimeClass(name, 0 if name == "su_CStringArray" else 1), {})
        converted[key] = target
        data = target.FieldsValue
        if name == "moHeader_c":
            data.update(fields(source, KHeaderFields))
        elif name == "moExtObject_c":
            data.update(fields(source, KExtLeadFields + KExtTailFields))
            data["shared"] = fields(source["shared"], KSharedFields)
            data["refcfg"] = fields(source["refcfg"], KRefCfgFields)
        elif name in ("moExtObjectList_c", "suObList", "moLogs_c"):
            data["items"] = tuple(node(row["o"]) for row in source["items"])
            if name == "moLogs_c":
                data.update(fields(source, KLogFields))
        elif name == "moStamp_c":
            data.update(fields(source, KStampFields))
        elif name == "moCStringHandle_c":
            data["value"] = wire_text(source["f08"])
        elif name == "su_CStringArray":
            data["values"] = tuple(wire_text(row["s"]) for row in source["items"])
        else:
            raise ValueError(f"unsupported object in generated header: {name}")
        return target

    return WriteHeadGraph(node(root), version)
