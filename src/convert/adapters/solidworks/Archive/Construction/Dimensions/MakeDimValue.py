from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import (
    MakeValueFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# existing distance construction retains its concrete native class while sharing complete dimension base field initialization
def MakeDimValue(OwnerValue: ArchiveNode, Parameter: ArchiveNode) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("ParallelPlaneDistanceDim_c", 1),
        MakeValueFields(OwnerValue, Parameter),
    )
