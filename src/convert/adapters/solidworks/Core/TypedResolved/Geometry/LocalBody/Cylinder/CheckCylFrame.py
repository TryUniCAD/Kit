from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylSpan import (
    CheckCylSpan,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


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
    CheckCylSpan(StartValue, EndValue, AxisValue, RadialValue)
    RadiusValue = MantleValue.FieldsValue["radius"]
    if (
        ReadXmtVector(MantleValue, "pvec") != StartValue
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
