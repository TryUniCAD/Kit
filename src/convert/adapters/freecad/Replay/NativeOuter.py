from __future__ import annotations

from collections.abc import Mapping

from convert.adapters.freecad.Errors.AdapterError import FreeCadAdapterA
from convert.adapters.freecad.Archive import (
    KMaxOuterFiles as MaxOuterFiles,
    KMaxTotalSize as MaxTotalSize,
)
from convert.adapters.freecad.Replay.MetadataTypes import IsPayloadMap, IsPayloadSeq
from convert.adapters.freecad.Replay.ReadOuterDoc import ReadOuterDoc
from interchange.Payloads.PayloadRoles import PayloadRole
from interchange.document.Models.DocumentModel import CadDocument


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
        SourceFile, Linked = ReadOuterDoc(Value)
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
