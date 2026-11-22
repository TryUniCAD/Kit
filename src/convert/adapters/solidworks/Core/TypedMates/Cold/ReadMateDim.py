from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.CheckMateParam import CheckMateParam


# the display handle binds the separately allocated distance driver to the mate
def ReadMateDim(NodeValue: ArchiveNode) -> ArchiveNode:
    Display = RequireNode(NodeValue.FieldsValue.get("f4b8"), "moDisplayDistanceDim_c")
    Handles = ReadRows(Display.FieldsValue.get("f850"))
    if len(Handles) != 1:
        raise ValueError("typed distance lacks one allocated dimension")
    Handle = RequireNode(Handles[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNode(Handle.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c")
    CheckMateParam(Handle, Dimension)
    return Dimension
