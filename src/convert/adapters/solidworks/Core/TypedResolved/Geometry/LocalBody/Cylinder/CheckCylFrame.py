from math import dist as Distance, isfinite as IsFinite

from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.geometry.Models.VectorSpace import SpaceVector


# the two supported rims must bound the same positively oriented analytic cylinder
def CheckCylFrame(
    MantleValue: XmtNode,
    NearPlane: XmtNode,
    FarPlane: XmtNode,
    NearCircle: XmtNode,
    FarCircle: XmtNode,
) -> None:
    StartValue = ReadXmtVector(NearPlane, "pvec")
    EndValue = ReadXmtVector(FarPlane, "pvec")
    AxisValue = ReadXmtVector(MantleValue, "axis")
    RadialValue = ReadXmtVector(MantleValue, "x_axis")
    StartPoint, AxisVector, Radial = (
        SpaceVector(*VectorValue)
        for VectorValue in (StartValue, AxisValue, RadialValue)
    )
    CheckSweepFrame(StartPoint, AxisVector, Radial)
    HeightValue = Distance(StartValue, EndValue)
    Projected = OffsetVector(StartPoint, AxisVector, HeightValue)
    RadiusValue = MantleValue.FieldsValue["radius"]
    if (
        not IsFinite(HeightValue)
        or HeightValue <= 0.0
        or Distance((Projected.x, Projected.y, Projected.z), EndValue)
        > 1e-14 * HeightValue
        or ReadXmtVector(MantleValue, "pvec") != StartValue
        or ReadXmtVector(FarPlane, "normal") != AxisValue
        or ReadXmtVector(FarPlane, "x_axis") != RadialValue
        or ReadXmtVector(NearPlane, "normal")
        != tuple(-Component for Component in AxisValue)
        or ReadXmtVector(NearPlane, "x_axis")
        != tuple(-Component for Component in RadialValue)
        or type(RadiusValue) is not float
        or not IsFinite(RadiusValue)
        or RadiusValue <= 0.0
        or RadiusValue != NearCircle.FieldsValue["radius"]
        or RadiusValue != FarCircle.FieldsValue["radius"]
    ):
        raise ValueError("local cylinder has inconsistent radius or signed frame")
