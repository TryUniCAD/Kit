from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# empty layer and mask owners must retain the real drawing without inventing active layers or copied visibility data
def MakeDrawLayers(OwnerValue: ArchiveNode) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moDrawing_c")
    MaskValue = ArchiveNode(
        RuntimeClass("moLayerMask_c", 1), {"f08": {"n": 0, "f18": 0, "data": bytes(0)}}
    )
    return ArchiveNode(
        RuntimeClass("moLayerMgr_c", 1),
        {
            "n": 0,
            "layers": (),
            "f08": None,
            "f30": OwnerValue,
            "f20": MaskValue,
            "f38": -1,
        },
    )
