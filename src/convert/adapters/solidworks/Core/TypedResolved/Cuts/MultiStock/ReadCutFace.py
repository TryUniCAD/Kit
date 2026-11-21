from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadFaceReps import (
    ReadFaceReps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved cut chooser face must bind both stock caps and sides and its actual cut circle to one external owner
def ReadCutFace(
    LinkValue: NativeLink,
    FaceValue: ArchiveNode,
    External: ArchiveNode,
    OwnerIds: tuple[int, int],
    LineMarks: frozenset[int],
    ArcMark: int,
) -> tuple[ArchiveNode, ...]:
    RepsValue = ReadFaceReps(FaceValue)
    Classes = tuple(Value.ClassValue.NameValue for Value in RepsValue)
    if len(set(RepsValue)) != 5 or Counter(Classes) != {
        "moFromSktEntSurfIdRep_c": 2,
        "moEndFaceSurfIdRep_c": 2,
        "moFromSktEnt3IntSurfIdRep_c": 1,
    }:
        raise ValueError("saved cut chooser has alternate surface representations")
    RefsValue = tuple(
        RequireNative(NativeRecord(Value.FieldsValue.get("f10")).get("f10"), "moFR_c")
        for Value in RepsValue
    )
    StockId, CutId = OwnerIds
    if len(set(RefsValue)) != 5 or any(
        RefValue.FieldsValue.get("f08") is not External
        or NativeRecord(RefValue.FieldsValue.get("f10")).get("f00")
        != (CutId if ClassName == "moFromSktEnt3IntSurfIdRep_c" else StockId)
        for RefValue, ClassName in zip(RefsValue, Classes, strict=True)
    ):
        raise ValueError(
            "saved cut chooser references a different producer or external owner"
        )
    Fields = tuple(Value.FieldsValue for Value in RepsValue)
    if (
        {
            (Value.get("f38"), Value.get("f3c"))
            for Value, ReprType in zip(Fields, Classes, strict=True)
            if ReprType == "moEndFaceSurfIdRep_c"
        }
        != {(0, 0), (1, 0)}
        or not {
            Value.get("f38")
            for Value, ReprType in zip(Fields, Classes, strict=True)
            if ReprType == "moFromSktEntSurfIdRep_c"
        }.issubset(LineMarks)
        or any(
            (Value.get("f38"), Value.get("f3c"), Value.get("f40")) != (ArcMark, -1, 0)
            for Value, ReprType in zip(Fields, Classes, strict=True)
            if ReprType == "moFromSktEnt3IntSurfIdRep_c"
        )
    ):
        raise ValueError("saved cut chooser disagrees with its actual profile markers")
    CheckTreeAlias(LinkValue, (*RepsValue, *RefsValue))
    return RepsValue
