from collections import Counter
from typing import Literal

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadFaceReps import (
    ReadFaceReps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved face carrier must resolve all of its constituent surfaces to the selected stock
def ReadStockRef(
    FaceValue: ArchiveNode,
    StockValue: ArchiveNode,
    SideCount: Literal[3, 4],
    *,
    LinkValue: NativeLink | None = None,
) -> ArchiveNode:
    RepsValue = ReadFaceReps(FaceValue)
    NamesValue = Counter(RepValue.ClassValue.NameValue for RepValue in RepsValue)
    if NamesValue != {
        "moFromSktEntSurfIdRep_c": SideCount,
        "moEndFaceSurfIdRep_c": 5 - SideCount,
    }:
        raise ValueError("two stock face carrier has alternate surface representations")
    RefsValue = tuple(
        RequireNative(
            NativeRecord(RepValue.FieldsValue.get("f10")).get("f10"), "moFR_c"
        )
        for RepValue in RepsValue
    )
    StockId = NativeNodeId(StockValue)
    ExtValues = {
        RequireNative(RefValue.FieldsValue.get("f08"), "moExtObject_c")
        for RefValue in RefsValue
    }
    if len(ExtValues) != 1 or any(
        NativeRecord(RefValue.FieldsValue.get("f10")).get("f00") != StockId
        for RefValue in RefsValue
    ):
        raise ValueError(
            "two stock face carrier does not resolve to its selected producer"
        )
    if LinkValue is not None:
        CheckTreeAlias(LinkValue, (FaceValue, *RepsValue, *RefsValue, *ExtValues))
    return next(iter(ExtValues))
