from __future__ import annotations

from convert.adapters.freecad.Errors.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Replay.MetadataTypes import IsPayloadMap
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.WireData import ValidateWireMap


# linked models need validation before they count against the native bundle limits
def ReadOuterDoc(Value: object) -> tuple[str, CadDocument]:
    if not IsPayloadMap(Value):
        raise FreeCadAdapterA("native FreeCAD external document metadata is invalid")
    SourceFile = str(Value.get("file", ""))
    Linked: object = Value.get("document")
    if IsPayloadMap(Linked):
        try:
            Linked = CadDocument.from_dict(ValidateWireMap(Linked))
        except (TypeError, ValueError, RecursionError) as ErrorInfo:
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            ) from ErrorInfo
    if not SourceFile or not isinstance(Linked, CadDocument):
        raise FreeCadAdapterA("native FreeCAD external document metadata is invalid")
    return SourceFile, Linked
