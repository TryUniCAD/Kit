from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
)
from convert.adapters.solidworks.Core.TypedMates.Cold.ReadMateDim import ReadMateDim
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# a distance mate owns a separate allocated dimension in addition to its feature identity
def ReadMateIds(NodeValue: ArchiveNode) -> tuple[int, ...]:
    MateId = NativeNodeId(NodeValue)
    if NodeValue.ClassValue.NameValue != "moMateDistanceDim_c":
        return (MateId,)
    Dimension = ReadMateDim(NodeValue)
    return MateId, FieldInt(Dimension.FieldsValue, "f50")
