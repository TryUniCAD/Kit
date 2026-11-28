from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    KHingeAxis,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# the selected local datum must retain concrete binary64 vector fields
def ReadPatPoint(PointValue: object) -> KDatumVector:
    Fields = RequireRecord(PointValue)
    if any(type(Fields.get(KeyValue)) is not float for KeyValue in ("x", "y", "z")):
        raise ValueError("pattern direction requires actual native datum coordinates")
    return ReadVector(Fields)


# the oblique line uses the actual rigid through origin datum and its oriented normal
def ReadPatFrame(Fields: Mapping[str, object]) -> PlaneFrame:
    Origin = ReadPatPoint(Fields.get("root"))
    Transform = RequireRecord(Fields.get("f20"))
    Matrix, Offset = ReadRigidXform(Transform)
    Horizontal = (Matrix[0], Matrix[3], Matrix[6])
    Vertical = (Matrix[1], Matrix[4], Matrix[7])
    Normal = (Matrix[2], Matrix[5], Matrix[8])
    if (
        FieldInt(Transform, "has_matrix") != 1
        or Origin != KHingeRoot
        or Offset != Origin
        or Horizontal != KHingeAxis
        or Normal != ReadPatPoint(Fields.get("normal"))
        or Normal[2] != 0.0
    ):
        raise ValueError(
            "pattern direction requires the actual bounded through-origin angular datum"
        )
    return PlaneFrame(Origin, Horizontal, Vertical, Normal)
