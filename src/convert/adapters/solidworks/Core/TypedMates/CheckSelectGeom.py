from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# detached absolute plane geometry must match both saved selection wrappers before its semantics can be admitted
def CheckSelectGeom(
    Selected: ArchiveNode, Resolved: ArchiveNode, PlaneValue: ArchiveNode
) -> None:
    DatumValue = RequireNode(PlaneValue.FieldsValue.get("ff8"), "moRefPlane_c")
    Absolute = RequireNode(DatumValue.FieldsValue.get("f6f8"), "moAbsoluteRefPlnData_c")
    if FieldInt(DatumValue.FieldsValue, "f08") != -1:
        raise ValueError("perpendicular detached plane has an allocated identity")
    for WrapperKey, PlaneKey in (("fd0", "root"), ("fe8", "normal")):
        SelectedValue = ReadVector(Selected.FieldsValue.get(WrapperKey))
        if SelectedValue != ReadVector(
            Resolved.FieldsValue.get(WrapperKey)
        ) or SelectedValue != ReadVector(Absolute.FieldsValue.get(PlaneKey)):
            raise ValueError("perpendicular detached selection geometry differs")
