from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    DatumDot,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# the first selected display supplies the finite endpoints of its contained through origin line
def AxisStations(
    PlaneValue: ArchiveNode, Frame: PlaneFrame, Direction: KDatumVector
) -> tuple[float, float]:
    Fields = RequireNode(
        PlaneValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    Picks = tuple(
        (Projection, FieldNames)
        for Basis, FieldNames in (
            (Frame.AxisU, ("b0", "b1")),
            (Frame.AxisV, ("b2", "b3")),
        )
        if (Projection := DatumDot(Basis, Direction))
    )
    if (
        len(Picks) != 1
        or abs(Picks[0][0]) != 1.0
        or DatumDot(Frame.NormalValue, Direction) != 0.0
    ):
        raise ValueError("axis must match an actual principal display direction")
    SignValue, FieldNames = Picks[0]
    Center = DatumDot(ReadVector(Fields.get("display_root")), Direction)
    Start, EndValue = sorted(
        Center + SignValue * RequireScalar(Fields.get(FieldName))
        for FieldName in FieldNames
    )
    if not Start < 0.0 < EndValue:
        raise ValueError(
            "the first finite principal plane must straddle the model origin"
        )
    return Start, EndValue
