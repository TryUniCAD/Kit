from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawBlocks import (
    MakeDrawBlocks,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawLayers import (
    MakeDrawLayers,
)


# the drawing tail must attach its actual active sheet and fresh empty managers before metadata serialization begins
def MakeDrawTail(
    OwnerValue: ArchiveNode, SheetValue: ArchiveNode, BuildValue: DrawBuild
) -> dict[str, object]:
    RequireRootNode(OwnerValue, "moDrawing_c")
    RequireRootNode(SheetValue, "moDrSheet")
    if SheetValue.FieldsValue["owner"] is not OwnerValue:
        raise ValueError("drawing root active sheet must belong to its actual model")
    return {
        "fe80": MakeDrawBlocks(
            OwnerValue,
            BuildValue.TargetValue,
            BuildValue.BlockValue,
            BuildValue.CreatedAt,
            BuildValue.FolderValue.BlocksName,
        ),
        "fed0": MakeDrawLayers(OwnerValue),
        "f1430": SheetValue,
        "f143c": 1,
        "f1444": 256 | int(BuildValue.AutoLink),
        "f1458": None,
        "f16a8": ArchiveNode(
            RuntimeClass("moDrwCompPropMgr_c", 1),
            {"f18": OwnerValue, "n10": 0, "f08": ()},
        ),
        "n1568": 0,
        "f1560": (),
        "n1578": 0,
        "f1570": (),
        "n1740": 0,
        "f14f8": {**EmptyRootRows(), "f38": 1},
        "zero_instance_blocks": EmptyRootRows(),
        "n1538": 0,
        "f1538": (),
    }
