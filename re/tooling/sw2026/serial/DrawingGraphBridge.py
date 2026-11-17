from __future__ import annotations

from collections.abc import Mapping

from Core import Obj
from builders.Definition import _model_definition
from builders.DrawingSheet import drawing_sheet
from builders.DrawingSheetObjects import sheet_ui_sketch
from defs.Drawing import DRAWING_CLSID
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields, KExtTailFields, KHeaderFields, KLogFields, KRefCfgFields,
    KSharedFields, KStampFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def project_generated_graph(source):
    converted = {}

    def text(value):
        if not isinstance(value, str):
            raise ValueError("generated drawing graph requires authored text")
        return CStringValue(value, True)

    def fields(owner, layout):
        result = {}
        for name, kind in layout:
            if kind == "bounds":
                present = owner["bboxflag"]
                if present not in (0, 1):
                    raise ValueError("generated drawing header has an invalid bounds flag")
                result[name] = tuple(owner[name][f"b{index}"] for index in range(10)) if present else None
            elif kind == "text":
                result[name] = text(owner[name])
            else:
                result[name] = value(owner[name])
        return result

    def value(owner):
        if isinstance(owner, ArchiveNode):
            key = id(owner)
            if key in converted:
                return converted[key]
            result = ArchiveNode(owner.ClassValue, {})
            converted[key] = result
            target = result.FieldsValue
            source = owner.FieldsValue
            name = owner.ClassValue.NameValue
            if name == "moHeader_c":
                target.update(fields(source, KHeaderFields))
            elif name == "moExtObject_c":
                target.update(fields(source, KExtLeadFields + KExtTailFields))
                target["shared"] = fields(source["shared"], KSharedFields)
                target["refcfg"] = fields(source["refcfg"], KRefCfgFields)
            elif name in ("suObList", "moExtObjectList_c", "moLogs_c"):
                target["items"] = tuple(value(row["o"]) for row in source["items"])
                if name == "moLogs_c":
                    target.update(fields(source, KLogFields))
            elif name == "moStamp_c":
                target.update(fields(source, KStampFields))
            elif name == "moCStringHandle_c":
                target["value"] = text(source["f08"])
            elif name == "su_CStringArray":
                target["values"] = tuple(text(row["s"]) for row in source["items"])
            else:
                target.update({name: value(field) for name, field in source.items()})
            return result
        if isinstance(owner, Mapping):
            return {name: value(field) for name, field in owner.items()}
        if isinstance(owner, (list, tuple)):
            return tuple(value(field) for field in owner)
        return owner

    return value(source)


def generated_document(*, construction, request):
    presentation = dict(request["presentation"]["definition"])
    presentation["tessellation"] = tuple(presentation["tessellation"])
    document = _model_definition(cls="uiDrawingDoc_c", clsid_a=DRAWING_CLSID[0], **presentation)
    document.f.update({
        "model": construction.model,
        "fac0": sheet_ui_sketch(settings=drawing_sheet(request["sheet"]), sheet=construction.model["f1430"]),
        "facc": 2, "drawing_end_marker": 0xDAF, "f16c8": 0, "f16dc": 0,
    })
    return project_generated_graph(document)
