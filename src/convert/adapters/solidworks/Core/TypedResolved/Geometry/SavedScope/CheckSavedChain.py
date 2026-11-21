from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# only one fully local saved chain can stand for the profile contour
def ReadSavedChain(ValueData: object) -> ArchiveNode:
    Envelope = NativeRecord(ValueData)
    RowsValue = NativeRows(Envelope.get("f2a8"))
    if Envelope.get("f2b0") != 1 or Envelope.get("n2a8") != 1 or len(RowsValue) != 1:
        raise ValueError(
            "SOLIDWORKS saved first boss requires one actual profile chain"
        )
    Chain = RequireNative(RowsValue[0].get("chain"), "moSketchChain_c")
    Fields = Chain.FieldsValue
    if (
        Fields.get("f60") != {"n": 1, "items": [{"v": 0}]}
        or any(
            Fields.get(NameValue) != 0
            for NameValue in ("flags", "nmap", "f90", "fa0", "fa4")
        )
        or Fields.get("end_map")
        or any(
            Fields.get(NameValue) is not None
            for NameValue in ("f30", "f40", "f48", "fc0", "fc8")
        )
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss has selected or trimmed chain owners"
        )
    return Chain


# cache traversal may rotate or reverse the same ring but cannot select different lines
def CheckSavedChain(
    LinkValue: NativeLink, ValueData: object, LoopValue: LineLoop
) -> None:
    ChainValue = ReadSavedChain(ValueData)
    CheckTreeAlias(LinkValue, (ChainValue,))
    Members = NativeRecord(ChainValue.FieldsValue.get("f08"))
    Claimed = tuple(RowValue.get("v") for RowValue in NativeRows(Members.get("items")))
    Ordered = tuple(
        LoopValue.LinesValue[Index].PermanentId for Index in LoopValue.OrderValue
    )
    if (
        Members.get("n") != 4
        or len(Claimed) != 4
        or any(type(Value) is not int for Value in Claimed)
    ):
        raise ValueError("SOLIDWORKS saved first boss has an alternate contour roster")
    if not any(
        Claimed == RingValue[Offset:] + RingValue[:Offset]
        for RingValue in (Ordered, Ordered[::-1])
        for Offset in range(4)
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss contour differs from its live profile"
        )
