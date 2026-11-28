from dataclasses import dataclass as DataClass
from math import (
    atan2 as CalcAngle,
    cos as CalcCos,
    dist as CalcDist,
    pi as PiValue,
    sin as CalcSin,
    ulp as CalcUlp,
)

from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwRims import (
    SwNativeRim,
)
from interchange.geometry.Models.VectorSpace import SpaceVector

# native rotations produce only a bounded few ulps of boundary closure residual
KAxisDrift = 64 * CalcUlp(1.0)


# each derived trim retains which cap and torus fins determine its orientation
@DataClass(frozen=True, slots=True)
class SwRimTrim:
    RimValue: SwNativeRim
    StationValue: float
    PhaseValue: float
    Direction: float
    OutwardSign: float


# signed torus and circle math consumes the actual typed vectors independently of index identity
def ReadSwVector(NodeValue: XmtNode, FieldName: str) -> SpaceVector:
    return SpaceVector(*ReadXmtVector(NodeValue, FieldName))


# oriented chart derivatives require unit parallel directions within the witnessed floating scale
def ReadAxisSign(First: SpaceVector, Second: SpaceVector) -> float:
    DotValue = DotVector(First, Second)
    if (
        any(
            not abs(DotVector(Value, Value) - 1.0) <= KAxisDrift
            for Value in (First, Second)
        )
        or not abs(abs(DotValue) - 1.0) <= KAxisDrift
    ):
        raise ValueError("SOLIDWORKS saved sweep trim has a foreign carrier direction")
    return 1.0 if DotValue > 0.0 else -1.0


# the rim chart is derived from the actual saved circle and opposing face incidence
def ReadSwTrim(TorusValue: XmtNode, RimValue: SwNativeRim) -> SwRimTrim:
    PlaneValue, CircleValue = RimValue.PlaneValue, RimValue.CircleValue
    Anchor = ReadSwVector(PlaneValue, "pvec")
    CircleAxis = ReadSwVector(CircleValue, "normal")
    RimAxis = ReadSwVector(CircleValue, "x_axis")
    if (
        Anchor != ReadSwVector(CircleValue, "centre")
        or CircleAxis != ReadSwVector(PlaneValue, "normal")
        or RimAxis != ReadSwVector(PlaneValue, "x_axis")
        or PlaneValue.String("sense") != "+"
        or CircleValue.String("sense") != "+"
        or CircleValue.FieldsValue["radius"] != TorusValue.FieldsValue["minor_radius"]
        or RimValue.CapValue.String("sense") != RimValue.CapFin.String("sense")
    ):
        raise ValueError("SOLIDWORKS saved sweep rim has a foreign cap chart or radius")
    CenterValue = ReadSwVector(TorusValue, "centre")
    MajorValue = RequireScalar(TorusValue.FieldsValue["major_radius"])
    AxisValue = ReadSwVector(TorusValue, "axis")
    FirstAxis = ReadSwVector(TorusValue, "x_axis")
    SecondAxis = CrossVector(AxisValue, FirstAxis)
    Position = OffsetVector(Anchor, CenterValue, -1.0)
    Station = CalcAngle(DotVector(Position, SecondAxis), DotVector(Position, FirstAxis))
    Radial = OffsetVector(
        OffsetVector(SpaceVector(0.0, 0.0, 0.0), FirstAxis, CalcCos(Station)),
        SecondAxis,
        CalcSin(Station),
    )
    Tangent = CrossVector(AxisValue, Radial)
    PhaseValue = CalcAngle(DotVector(RimAxis, AxisValue), DotVector(RimAxis, Radial))
    Direction = ReadAxisSign(CircleAxis, CrossVector(Radial, AxisValue))
    OutwardSign = ReadAxisSign(CircleAxis, Tangent) * FinSign(RimValue.CapFin)
    CheckRimChart(
        Anchor,
        OffsetVector(CenterValue, Radial, MajorValue),
        RimAxis,
        Tangent,
        MajorValue,
        Direction,
        OutwardSign,
        RimValue.WallFin,
    )
    return SwRimTrim(RimValue, Station, PhaseValue, Direction, OutwardSign)


# native fin signs carry the direction of traversal through both oriented face charts
def FinSign(FinValue: XmtNode) -> float:
    return 1.0 if FinValue.String("sense") == "+" else -1.0


# circle position and orthonormal frame determine a unique analytic trim direction and phase
def CheckRimChart(
    Anchor: SpaceVector,
    Predicted: SpaceVector,
    RimAxis: SpaceVector,
    Tangent: SpaceVector,
    MajorValue: float,
    Direction: float,
    OutwardSign: float,
    WallFin: XmtNode,
) -> None:
    if (
        not CalcDist(
            (Anchor.x, Anchor.y, Anchor.z), (Predicted.x, Predicted.y, Predicted.z)
        )
        <= 64 * CalcUlp(MajorValue)
        or not abs(DotVector(RimAxis, Tangent)) <= KAxisDrift
        or not abs(DotVector(RimAxis, RimAxis) - 1.0) <= KAxisDrift
        or Direction * FinSign(WallFin) != OutwardSign
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep rim does not close on its torus meridian"
        )


# outward caps select the witnessed quarter interval rather than its periodic complement
def CheckSwTrims(FirstTrim: SwRimTrim, SecondTrim: SwRimTrim) -> None:
    StartValue, EndValue = sorted((FirstTrim, SecondTrim), key=GetSwStation)
    if (
        not abs(StartValue.StationValue + PiValue / 2.0) <= KAxisDrift
        or not abs(EndValue.StationValue) <= KAxisDrift
        or (StartValue.OutwardSign, EndValue.OutwardSign) != (-1.0, 1.0)
    ):
        raise ValueError("SOLIDWORKS saved sweep does not own this signed quarter trim")


# geometrical station orders trim uses independently of storage allocation and iteration order
def GetSwStation(TrimValue: SwRimTrim) -> float:
    return TrimValue.StationValue
