from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeDrawFeature import (
    MakeDrawFeature,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ScaleFrame import (
    MakeScaleFrame,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DetailFields import (
    KDetailFields,
)


# every detail folder collection needs its native empty owner without introducing annotation defaults
def MakeSheetDetail(SheetValue: ArchiveNode, BuildValue: SheetBuild) -> ArchiveNode:
    FolderValue = MakeDrawFeature(
        "moDetailFolder_c",
        BuildValue.NamesValue.DetailName,
        SheetValue,
        BuildValue.FirstIdValue + 3,
        BuildValue,
    )
    for RuleValue in KDetailFields["moDetailFolder_c"]:
        if RuleValue.KindValue == "Embed" and RuleValue.TypeValue == "rf.suObList":
            FolderValue.FieldsValue[RuleValue.NameValue] = {"n": 0, "items": ()}
    FolderValue.FieldsValue.update(
        {"fd90": MakeScaleFrame(1.0), "fd78": None, "has_fd98": 0, "fde8": 0}
    )
    return FolderValue
