from convert.adapters.solidworks.Archive.Construction.Model.RequireModel import (
    RequireModel,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a fresh model self component must retain the actual owner rather than duplicate its fields or persistent identifier
def MakeSelfComp(OwnerValue: ArchiveNode) -> ArchiveNode:
    RequireModel(OwnerValue)
    return ArchiveNode(
        RuntimeClass("moUnitComponent_c", 1), {"owner": OwnerValue, "has_ext": 0}
    )
