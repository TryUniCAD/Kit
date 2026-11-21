from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
)


# the live length parameter preserves driving intent when a display cache is empty
def ReadDistance(MateNode: ArchiveNode) -> float:
    Display = RequireNode(MateNode.FieldsValue.get("f4b8"), "moDisplayDistanceDim_c")
    Handles = ReadRows(Display.FieldsValue.get("f850"))
    if len(Handles) != 1:
        raise ValueError("the driving distance lacks its single native handle")
    Handle = RequireNode(Handles[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNode(Handle.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c")
    Parameter = RequireNode(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    Distance = RequireScalar(Parameter.FieldsValue.get("f58"))
    if Distance <= 0:
        raise ValueError("the ordinary driving distance must be positive")
    return Distance
