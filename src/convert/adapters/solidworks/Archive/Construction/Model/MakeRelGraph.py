from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireModel import (
    RequireModel,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh relation bookkeeping must belong to the actual model without borrowing saved relations or cached values
def MakeRelGraph(OwnerValue: ArchiveNode) -> ArchiveNode:
    RequireModel(OwnerValue)
    return ArchiveNode(
        RuntimeClass("moRelMgr_c", 1),
        {
            "owner": OwnerValue,
            "f58": EmptyRootRows(),
            "f10": EmptyRootRows(),
            "f170": "",
            "f178": 0,
            "f180": 0,
            "f150": 0,
            "ff4": -1,
            "fa0": EmptyRootRows(),
            "f1b0": -1,
            "n1c0": 0,
            "f1c0": (),
        },
    )
