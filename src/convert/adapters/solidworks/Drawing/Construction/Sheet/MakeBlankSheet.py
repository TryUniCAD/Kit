from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckSheetBuild import (
    CheckSheetBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckSheetOwner import (
    CheckSheetOwner,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeDrawFeature import (
    MakeDrawFeature,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetDetail import (
    MakeSheetDetail,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetOwn import (
    MakeSheetOwn,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetPlane import (
    MakeSheetPlane,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetRef import (
    MakeSheetRef,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetSketch import (
    MakeSheetSketch,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ScaleFrame import (
    MakeScaleFrame,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetGraph import SheetGraph


# a neutral sheet must allocate its complete support graph before the definition serializer sees it
def MakeBlankSheet(
    BuildValue: SheetBuild, OwnerValue: ArchiveNode, ComponentValue: ArchiveNode
) -> SheetGraph:
    CheckSheetBuild(BuildValue)
    CheckSheetOwner(OwnerValue, ComponentValue)
    SheetValue = MakeDrawFeature(
        "moDrSheet",
        BuildValue.InputValue.NameValue,
        OwnerValue,
        BuildValue.FirstIdValue,
        BuildValue,
    )
    PlaneValue = MakeSheetPlane(SheetValue, BuildValue)
    PlaneReference = MakeSheetRef(PlaneValue, OwnerValue, BuildValue.ArchiveVersion)
    PlaneValue.FieldsValue["f08"] = BuildValue.FirstIdValue + 1
    ProfileValue = MakeSheetSketch(SheetValue, PlaneReference, BuildValue)
    DetailValue = MakeSheetDetail(SheetValue, BuildValue)
    Supports = (PlaneValue, ProfileValue, DetailValue)
    SheetValue.FieldsValue.update(MakeSheetOwn(BuildValue, ProfileValue, DetailValue))
    SheetValue.FieldsValue["f60"] = {
        "list": {
            "n": len(Supports),
            "items": tuple({"o": ChildValue} for ChildValue in Supports),
        },
        "tail": 0,
    }
    for NodeValue in (SheetValue, *Supports):
        NodeValue.FieldsValue["f0c"] = (
            CastValue(int, NodeValue.FieldsValue["f0c"]) & 4294803448
        )
    UiSketch = ArchiveNode(
        RuntimeClass("uoSketch", 1),
        {
            "profile_feature_id": ProfileValue.FieldsValue["f08"],
            "f80": MakeScaleFrame(
                BuildValue.InputValue.NumeratorValue
                / BuildValue.InputValue.DenominatorValue
            ),
        },
    )
    return SheetGraph(
        SheetValue,
        PlaneValue,
        ProfileValue,
        DetailValue,
        UiSketch,
        BuildValue.FirstIdValue + 4,
    )
