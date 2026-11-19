from __future__ import annotations

from collections.abc import Mapping

from convert.adapters.freecad.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Archive import (
    KMaxOuterFiles as MaxOuterFiles,
    KMaxTotalSize as MaxTotalSize,
)
from convert.adapters.freecad.Replay.MetadataTypes import IsPayloadMap, IsPayloadSeq
from interchange.Payloads.PayloadRoles import PayloadRole
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.WireData import ValidateWireMap


# this definition exists because focused behavior needs one stable owner
def PayloadSize(DocValue: CadDocument) -> int:
    Total = 0
    for Payload in DocValue.BrepPayloads:
        DataValue = Payload.PayloadData
        if Payload.ValueRole == PayloadRole.DOCUMENT and DataValue is not None:
            Total += len(DataValue)
    return Total


# this definition exists because focused behavior needs one stable owner
def NativeOuter(DocValue: CadDocument) -> list[tuple[str, CadDocument]]:
    MetaValue = DocValue.metadata
    FreecadValue: object = MetaValue.get("freecad")
    Freecad: Mapping[str, object] = FreecadValue if IsPayloadMap(FreecadValue) else {}
    Values: object = Freecad.get("external_documents")
    if Values is None:
        Values = []
    if not IsPayloadSeq(Values):
        raise FreeCadAdapterA("native FreeCAD external document metadata is invalid")
    Result: list[tuple[str, CadDocument]] = []
    SeenValue: set[str] = set()
    Total = 0
    for Value in Values:
        if not IsPayloadMap(Value):
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            )
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
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            )
        if SourceFile in SeenValue:
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata contains duplicates"
            )
        SeenValue.add(SourceFile)
        Total += PayloadSize(Linked)
        if len(Result) >= MaxOuterFiles or Total > MaxTotalSize:
            raise FreeCadAdapterA(
                "native FreeCAD external documents exceed safe limits"
            )
        Result.append((SourceFile, Linked))
    return Result
