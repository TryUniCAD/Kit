from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import (
    RevFaceRef,
)


# saved neighbouring cylindrical and end representations own typed feature references
def ReadRevFace(
    LinkValue: NativeLink,
    FaceValue: ArchiveNode,
    Epochs: Mapping[int, int],
    CountValue: int,
    Flags: int,
) -> tuple[RevFaceRef, ...]:
    Fields = RequireNative(FaceValue, "moFaceRef_c").FieldsValue
    RowsValue = tuple(RowValue.get("f08") for RowValue in NativeRows(Fields.get("f10")))
    if (
        len(RowsValue) != CountValue
        or Fields.get("f08") != CountValue
        or Fields.get("fe8") != Flags
        or (
            tuple(Index for Index, Value in enumerate(RowsValue) if Value is None)
            != ((2, 4) if CountValue == 5 else (5,))
        )
        or Fields.get("has_f18") != 0
        or Fields.get("nf0") != 0
    ):
        raise ValueError("selected revolve cut face has alternate incidence")
    Result: list[RevFaceRef] = []
    References: list[ArchiveNode] = []
    for Value in RowsValue:
        if Value is None:
            continue
        RepValue = RequireNative(Value)
        ClassName = RepValue.ClassValue.NameValue
        IsEnd = ClassName == "moEndFaceSurfIdRep_c"
        if ClassName not in ("moFromSktEntSurfIdRep_c", "moEndFaceSurfIdRep_c") or (
            IsEnd and RepValue.FieldsValue.get("f3c") != 0
        ):
            raise ValueError("selected revolve cut face has an alternate surface owner")
        RefValue = RequireNative(
            NativeRecord(RepValue.FieldsValue.get("f10")).get("f10"), "moFR_c"
        )
        External = RequireNative(RefValue.FieldsValue.get("f08"), "moExtObject_c")
        Feature = NativeRecord(RefValue.FieldsValue.get("f10"))
        FeatureId = FieldInt(Feature, "f00")
        if Feature.get("f08") != Epochs.get(FeatureId) or FeatureId not in Epochs:
            raise ValueError(
                "selected revolve cut face has a different feature creation owner"
            )
        References.append(RefValue)
        Result.append(
            RevFaceRef(
                RepValue,
                External,
                FeatureId,
                IsEnd,
                FieldInt(RepValue.FieldsValue, "f38"),
            )
        )
    if len(set(References)) != len(References) or len(
        {Value.Representation for Value in Result}
    ) != len(Result):
        raise ValueError(
            "selected revolve cut face repeats a representation or feature reference"
        )
    CheckTreeAlias(
        LinkValue,
        (
            FaceValue,
            *References,
            *(Value.Representation for Value in Result),
            *(Value.ExternalValue for Value in Result),
        ),
    )
    return tuple(Result)
