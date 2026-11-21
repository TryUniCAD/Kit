from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.CheckMateParam import CheckMateParam
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# a distance mate owns a separate allocated dimension in addition to its feature identity
def ReadMateIds(NodeValue: ArchiveNode) -> tuple[int, ...]:
    MateId = NativeNodeId(NodeValue)
    if NodeValue.ClassValue.NameValue != "moMateDistanceDim_c":
        return (MateId,)
    Display = RequireNode(NodeValue.FieldsValue.get("f4b8"), "moDisplayDistanceDim_c")
    Handles = ReadRows(Display.FieldsValue.get("f850"))
    if len(Handles) != 1:
        raise ValueError("typed distance lacks one allocated dimension")
    Handle = RequireNode(Handles[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNode(Handle.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c")
    CheckMateParam(Handle, Dimension)
    return MateId, FieldInt(Dimension.FieldsValue, "f50")
