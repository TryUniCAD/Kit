from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Partition.LocalCylinder.BoreVectors import (
    KBoreVec,
    MakeBoreVec,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckBoreFit import (
    CheckBoreFit,
    KBoreRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckBorePair import (
    CheckBorePair,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the physical radius must be a finite value in the local analytic domain
def ReadBoreRadius(NodeValue: XmtNode) -> float:
    Radius = NodeValue.FieldsValue["radius"]
    if type(Radius) is not float or not 0.0 < Radius <= 1000000.0:
        raise ValueError("local circular rim has an invalid stored radius")
    return Radius


# reciprocal fins identify the actual supporting plane and paired wall for each circle
def ReadRimOwner(NodesValue: Mapping[int, XmtNode], FinValue: XmtNode) -> XmtNode:
    LoopValue = NodesValue[FinValue.Integer("loop")]
    FaceValue = NodesValue[LoopValue.Integer("face")]
    return NodesValue[FaceValue.Integer("surface")]


# stored circle centres must join their actual plane and wall before projection
def ReadWireRims(
    NodesValue: Mapping[int, XmtNode], CurvesValue: tuple[XmtNode, ...]
) -> dict[tuple[int, int], KPrismVector]:
    Centres: dict[tuple[int, int], KPrismVector] = {}
    for Circle in CurvesValue:
        EdgeValue = NodesValue[Circle.Integer("owner")]
        FinValue = NodesValue[EdgeValue.Integer("halfedge")]
        First = ReadRimOwner(NodesValue, FinValue)
        Second = ReadRimOwner(NodesValue, NodesValue[FinValue.Integer("other")])
        CapValue, WallValue = (
            (First, Second) if First.KindValue == 50 else (Second, First)
        )
        Centre = ReadXmtVector(Circle, "centre")
        PairValue = CapValue.IndexValue, WallValue.IndexValue
        if (
            (CapValue.KindValue, WallValue.KindValue) != (50, 51)
            or PairValue in Centres
            or not all(IsFinite(Value) for Value in Centre)
            or ReadBoreRadius(Circle) != ReadBoreRadius(WallValue)
        ):
            raise ValueError("local circular rim has a contradictory stored owner")
        Centres[PairValue] = Centre
    return Centres


# both cap stations need an independently linked raw centre for this wall
def ReadWirePair(
    WallValue: XmtNode,
    PlanesValue: tuple[XmtNode, XmtNode],
    CapOrigins: tuple[KPrismVector, KPrismVector],
    RimValues: Mapping[tuple[int, int], KPrismVector],
    AxisValue: KBoreVec,
) -> KBoreRing:
    First, Second = PlanesValue
    NearRim = RimValues.get((First.IndexValue, WallValue.IndexValue))
    FarRim = RimValues.get((Second.IndexValue, WallValue.IndexValue))
    if NearRim is None or FarRim is None:
        raise ValueError("local circular wall has an incomplete stored rim pair")
    CheckBorePair(
        (NearRim, FarRim),
        CapOrigins,
        ReadXmtVector(WallValue, "pvec"),
        AxisValue,
        1.0,
    )
    return NearRim, ReadBoreRadius(WallValue)


# normalized reader directions may not mask a contradictory stored wall or plane axis
def CheckWireAxes(NodesValue: Mapping[int, XmtNode], OuterAxis: KPrismVector) -> None:
    AxesValue = (OuterAxis, tuple(-Value for Value in OuterAxis))
    for NodeValue in NodesValue.values():
        if (
            NodeValue.KindValue in (31, 50, 51)
            and ReadXmtVector(
                NodeValue, "axis" if NodeValue.KindValue == 51 else "normal"
            )
            not in AxesValue
        ):
            raise ValueError("local circular bore axes must follow both cap stations")


# comparison before unit conversion prevents colliding wire geometry from rounding apart
def CheckWireBores(
    NodesValue: Mapping[int, XmtNode], CurvesValue: tuple[XmtNode, ...]
) -> None:
    RimValues = ReadWireRims(NodesValue, CurvesValue)
    First, Second = (Value for Value in NodesValue.values() if Value.KindValue == 50)
    PlanesValue = First, Second
    CapOrigins = ReadXmtVector(First, "pvec"), ReadXmtVector(Second, "pvec")
    WallValues = tuple(Value for Value in NodesValue.values() if Value.KindValue == 51)
    OuterWall = max(WallValues, key=ReadBoreRadius)
    OuterAxis = ReadXmtVector(OuterWall, "axis")
    CheckWireAxes(NodesValue, OuterAxis)
    AxisValue = MakeBoreVec(OuterAxis)
    if any(
        RimValues.get((Plane.IndexValue, OuterWall.IndexValue)) != Origin
        for Plane, Origin in zip(PlanesValue, CapOrigins, strict=True)
    ):
        raise ValueError("local circular stock rim is displaced from its stored cap")
    StockRing = ReadWirePair(OuterWall, PlanesValue, CapOrigins, RimValues, AxisValue)
    BoreRings = tuple(
        ReadWirePair(Value, PlanesValue, CapOrigins, RimValues, AxisValue)
        for Value in WallValues
        if Value is not OuterWall
    )
    CheckBoreFit(StockRing, BoreRings, 1.0)
