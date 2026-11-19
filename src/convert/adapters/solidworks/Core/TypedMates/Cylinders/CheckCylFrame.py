from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylEndpoint import (
    CylEndpoint,
)
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame


# the actual cylinder fixes the carrier line while the selected wrapper owns its signed direction
def CheckCylFrame(Endpoint: CylEndpoint, ChildValue: CylChild) -> None:
    Matrix = ReadMateFrame(Endpoint.ItemValue.transform)
    LocalPoint = ReadXmtVector(ChildValue.SurfaceValue, "pvec")
    CarrierAxis = ReadXmtVector(ChildValue.SurfaceValue, "axis")
    LocalAxis = Endpoint.LocalAxisValue
    AxisSign = -1.0 if DotVector(LocalAxis, CarrierAxis) < 0.0 else 1.0
    Expected = tuple(
        sum(
            LocalPoint[AxisIndex] * Matrix[AxisIndex * 4 + Index]
            for AxisIndex in range(3)
        )
        + Matrix[12 + Index]
        for Index in range(3)
    )
    Expected += tuple(
        sum(
            LocalAxis[AxisIndex] * Matrix[AxisIndex * 4 + Index]
            for AxisIndex in range(3)
        )
        for Index in range(3)
    )
    Actual = (*Endpoint.OriginValue, *Endpoint.AxisValue)
    Radius = RequireScalar(ChildValue.SurfaceValue.FieldsValue.get("radius"))
    if (
        Radius <= 0
        or not IsClose(Endpoint.RadiusValue, Radius, rel_tol=1e-10, abs_tol=1e-12)
        or not all(
            IsClose(LeftValue, RightValue, rel_tol=1e-10, abs_tol=1e-12)
            for LeftValue, RightValue in zip(Actual, Expected, strict=True)
        )
        or not all(
            IsClose(LocalValue, AxisSign * CarrierValue, rel_tol=1e-10, abs_tol=1e-12)
            for LocalValue, CarrierValue in zip(LocalAxis, CarrierAxis, strict=True)
        )
        or not all(
            IsClose(DotVector(Value, Value), 1.0, rel_tol=1e-10, abs_tol=1e-12)
            for Value in (LocalAxis, CarrierAxis)
        )
    ):
        raise ValueError(
            "concentric cylinder geometry or local axis differs from its actual child and occurrence"
        )
