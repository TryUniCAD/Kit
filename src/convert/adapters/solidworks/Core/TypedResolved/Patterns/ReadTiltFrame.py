from collections.abc import Mapping
from math import cos as Cosine, dist as Distance, sin as SinValue

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the known hinge angle must reproduce the stored frame and the ordered finite display border
def ReadTiltFrame(
    Fields: Mapping[str, object],
    AngleValue: float,
    StartValue: tuple[float, float, float],
    EndValue: tuple[float, float, float],
) -> tuple[PlaneFrame, tuple[float, float, float]]:
    Origin = ReadVector(Fields.get("root"))
    Matrix, Offset = ReadRigidXform(NativeRecord(Fields.get("f20")))
    First = (Matrix[0], Matrix[3], Matrix[6])
    Second = (Matrix[1], Matrix[4], Matrix[7])
    Normal = (Matrix[2], Matrix[5], Matrix[8])
    if (
        Origin != (0.0, 0.0, 0.0)
        or Offset != Origin
        or First != (0.0, 0.0, -1.0)
        or Normal != ReadVector(Fields.get("normal"))
        or Distance(Second, (SinValue(AngleValue), Cosine(AngleValue), 0.0)) > 2e-15
        or Distance(Normal, (Cosine(AngleValue), -SinValue(AngleValue), 0.0)) > 2e-15
    ):
        raise ValueError("angular datum transform contradicts the live drive angle")
    LowValue, HighValue = -StartValue[2], -EndValue[2]
    Length = HighValue - LowValue
    Margin = Length * 0.05
    Borders = tuple(RequireScalar(Fields.get(f"b{Index}")) for Index in range(4))
    Expected = (HighValue + Margin, LowValue - Margin, Length + Margin, -Margin)
    if Length <= 1e-7 or Distance(Borders, Expected) > 2e-15:
        raise ValueError("angular datum border contradicts the finite hinge")
    LeftValue, RightValue, UpperValue, LowerValue = Borders
    AlongU = (LeftValue + RightValue) * 0.5
    AlongV = (UpperValue + LowerValue) * 0.5
    CenterValue = (
        AlongU * First[0] + AlongV * Second[0],
        AlongU * First[1] + AlongV * Second[1],
        AlongU * First[2] + AlongV * Second[2],
    )
    return PlaneFrame(Origin, First, Second, Normal), CenterValue
