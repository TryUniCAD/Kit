from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylEndpoint import (
    CylEndpoint,
)
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame


# source cylinder geometry must agree with its actual child and independently rigid occurrence placement
def CheckCylFrame(
    Endpoint: CylEndpoint, Wrapper: ArchiveNode, ChildValue: CylChild
) -> None:
    Matrix = ReadMateFrame(Endpoint.ItemValue.transform)
    LocalPoint = ReadXmtVector(ChildValue.SurfaceValue, "pvec")
    LocalAxis = ReadXmtVector(ChildValue.SurfaceValue, "axis")
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
        or ReadVector(Wrapper.FieldsValue.get("f108")) != LocalAxis
        or not IsClose(
            sum(Value * Value for Value in LocalAxis), 1.0, rel_tol=1e-10, abs_tol=1e-12
        )
    ):
        raise ValueError(
            "concentric cylinder geometry or local axis differs from its actual child and occurrence"
        )
