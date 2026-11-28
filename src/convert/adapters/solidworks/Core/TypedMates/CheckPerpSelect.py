from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedMates.CheckSelectGeom import CheckSelectGeom


# detached selections must retain the owning assembly and original datum without masquerading as registered resolved wrappers
def CheckPerpSelect(
    Selected: ArchiveNode, Resolved: ArchiveNode, ModelValue: ArchiveNode
) -> None:
    Fields = Selected.FieldsValue
    PlaneValue = RequireNode(Fields.get("f58"), "moCompRefPlane_c")
    PlaneFields = PlaneValue.FieldsValue
    UnitValue = RequireNode(PlaneFields.get("f58"), "moUnitComponent_c")
    ActualPlane = RequireNode(Resolved.FieldsValue.get("f58"), "moCompRefPlane_c")
    if (
        UnitValue.FieldsValue.get("owner") is not ModelValue
        or FieldInt(UnitValue.FieldsValue, "has_ext") != 0
        or FieldInt(Fields, "f50") != 0
        or FieldInt(Fields, "f68") != 1
        or FieldInt(Fields, "f70") != 19000
        or any(
            FieldInt(Fields, FieldName) != -12345 for FieldName in ("f74", "f78", "f7c")
        )
        or FieldInt(PlaneFields, "f100") != 0
        or FieldInt(RequireRecord(PlaneFields.get("ff0")), "f00") != -1
        or FieldInt(RequireRecord(PlaneFields.get("ff0")), "f08") != 2592000
        or FieldInt(PlaneFields, "f9c")
        != FieldInt(RequireRecord(ActualPlane.FieldsValue.get("ff0")), "f00")
        or FieldInt(ActualPlane.FieldsValue, "f9c") != -1
    ):
        raise ValueError("perpendicular detached selection ownership is inconsistent")
    CheckSelectGeom(Selected, Resolved, PlaneValue)
