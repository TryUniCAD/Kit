from dataclasses import dataclass as DataClass
from math import tau as FullTurn

from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Curves.BrepPcurves import CirclePcurve, LinePcurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
    BrepVertex,
)
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# one periodic rim shares a full spatial circle between torus and cap parameter spaces
@DataClass(frozen=True, slots=True)
class TubeRim:
    CurveValue: CircleCurve
    CapValue: PlaneSurface
    VertexValue: BrepVertex
    EdgeValue: BrepEdge
    CapFace: BrepFace
    LoopValues: tuple[BrepLoop, BrepLoop]
    UseValues: tuple[BrepCoedge, BrepCoedge]
    PCurveValues: tuple[CirclePcurve, LinePcurve]


# the two edge uses have opposite orientations and periodic seams are representational anchors
def MakeTubeRim(
    Prefix: str,
    CenterValue: SpaceVector,
    NormalValue: SpaceVector,
    RadialValue: SpaceVector,
    RadiusValue: float,
    StationValue: float,
    TurnSense: float,
) -> TubeRim:
    CurveValue = CircleCurve(
        f"{Prefix}-circle", CenterValue, NormalValue, RadialValue, RadiusValue
    )
    PlaneValue = PlaneSurface(f"{Prefix}-plane", CenterValue, NormalValue, RadialValue)
    VertexValue = BrepVertex(
        f"{Prefix}-seam",
        OffsetVector(CenterValue, RadialValue, RadiusValue),
        attributes={"periodic_seam": True},
    )
    EdgeValue = BrepEdge(
        f"{Prefix}-edge", VertexValue.id, VertexValue.id, CurveValue.id, 0.0, FullTurn
    )
    CapCurve = CirclePcurve(f"{Prefix}-cap-uv", PlaneVector(0.0, 0.0), RadiusValue)
    WallCurve = LinePcurve(
        f"{Prefix}-wall-uv", PlaneVector(StationValue, 0.0), PlaneVector(0.0, TurnSense)
    )
    CapUse = BrepCoedge(f"{Prefix}-cap-use", EdgeValue.id, CapCurve.id)
    WallUse = BrepCoedge(
        f"{Prefix}-wall-use", EdgeValue.id, WallCurve.id, reversed=True
    )
    CapLoop = BrepLoop(f"{Prefix}-cap-loop", (CapUse.id,), outer=True)
    WallLoop = BrepLoop(f"{Prefix}-wall-loop", (WallUse.id,))
    return TubeRim(
        CurveValue,
        PlaneValue,
        VertexValue,
        EdgeValue,
        BrepFace(f"{Prefix}-cap", PlaneValue.id, (CapLoop.id,)),
        (CapLoop, WallLoop),
        (CapUse, WallUse),
        (CapCurve, WallCurve),
    )
