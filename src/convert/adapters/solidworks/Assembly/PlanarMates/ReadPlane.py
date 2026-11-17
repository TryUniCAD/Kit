from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)


# projected frame values come from the concrete wrapper rather than display names
def ReadVector(VectorValue: object) -> tuple[float, float, float]:
    Coordinates = RequireRecord(VectorValue)
    return (
        RequireScalar(Coordinates.get("x")),
        RequireScalar(Coordinates.get("y")),
        RequireScalar(Coordinates.get("z")),
    )


# detached fallback geometry must not stand in for the actual selected child plane
def ReadPlane(Wrapper: ArchiveNode, MateId: int, OrderValue: int) -> ArchiveNode:
    Fields = Wrapper.FieldsValue
    if (
        FieldInt(Fields, "f74") != MateId
        or FieldInt(Fields, "f78") != OrderValue
        or FieldInt(Fields, "f7c") != OrderValue
    ):
        raise ValueError("the resolved plane wrapper has inconsistent ownership")
    Plane = RequireNode(Fields.get("f58"), "moCompRefPlane_c")
    if "ff8" not in Plane.FieldsValue or Plane.FieldsValue["ff8"] is not None:
        raise ValueError("resolved plane owns an unexpected target")
    return Plane
