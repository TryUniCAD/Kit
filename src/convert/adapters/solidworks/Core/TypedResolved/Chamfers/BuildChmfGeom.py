from dataclasses import replace as ReplaceValue
from math import tan as Tangent

from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfEdgeRead,
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import (
    BuildPrismGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# the cut removes an exact right triangle from the selected signed rectangular corner
def ChmfCutRing(
    EdgeValue: ChmfEdgeRead,
    DistanceMm: float,
    OtherMm: float,
) -> tuple[LineGeometry, ...]:
    Along = EdgeValue.EdgeAxis
    AxisU, AxisV = (Along + 1) % 3, (Along + 2) % 3
    Bounds = EdgeValue.BoundsValue
    Lower, Upper = CoordsChmf(Bounds.minimum), CoordsChmf(Bounds.maximum)
    Primary = EdgeValue.DistanceAxis
    Other = AxisV if Primary == AxisU else AxisU
    LegValues = {Primary: DistanceMm, Other: OtherMm}
    if any(
        not 0.0 < LegValues[AxisIndex] < Upper[AxisIndex] - Lower[AxisIndex]
        for AxisIndex in (AxisU, AxisV)
    ):
        raise ValueError("chamfer setbacks leave their actual incident stock faces")
    StockRing = (
        (Lower[AxisU], Lower[AxisV]),
        (Upper[AxisU], Lower[AxisV]),
        (Upper[AxisU], Upper[AxisV]),
        (Lower[AxisU], Upper[AxisV]),
    )
    CornerBits = EdgeValue.CornerBits
    Corner = StockRing[((0, 3), (1, 2))[CornerBits[AxisU]][CornerBits[AxisV]]]
    Index = StockRing.index(Corner)
    Clipped = tuple(
        ChmfClip(Corner, Neighbor, (LegValues[AxisU], LegValues[AxisV]))
        for Neighbor in (StockRing[Index - 1], StockRing[(Index + 1) % len(StockRing)])
    )
    Points = tuple(
        PlaneVector(*Value)
        for Value in (*StockRing[:Index], *Clipped, *StockRing[Index + 1 :])
    )
    return tuple(
        LineGeometry(First, Other)
        for First, Other in zip(Points, Points[1:] + Points[:1], strict=True)
    )


# each setback travels along the original incident face toward its opposite edge
def ChmfClip(
    Corner: tuple[float, float],
    Neighbor: tuple[float, float],
    LegValues: tuple[float, float],
) -> tuple[float, float]:
    First, Other = (
        Coord + (Setback if EndValue > Coord else -Setback if EndValue < Coord else 0.0)
        for Coord, EndValue, Setback in zip(Corner, Neighbor, LegValues, strict=True)
    )
    return First, Other


# a principal edge determines the exact world transform of the clipped cross section
def ChmfPrism(
    LinkValue: NativeLink, Owners: ChmfOwners, EdgeValue: ChmfEdgeRead
) -> PrismPlan:
    Along = EdgeValue.EdgeAxis
    Lower, Upper = CoordsChmf(EdgeValue.BoundsValue.minimum), CoordsChmf(
        EdgeValue.BoundsValue.maximum
    )
    AxisU, AxisV, AxisZ = (
        SpaceVector(*(float(Other == AxisIndex) for Other in range(3)))
        for AxisIndex in ((Along + 1) % 3, (Along + 2) % 3, Along)
    )
    FrameValue = Transform(
        SpaceVector(*(Lower[Along] if Index == Along else 0.0 for Index in range(3))),
        AxisU,
        AxisV,
        AxisZ,
    )
    DistanceMm = Owners.Distance.ValueSi * 1000.0
    AngleValue, SecondValue = Owners.AngleValue, Owners.SecondValue
    OtherMm = DistanceMm
    if AngleValue is not None:
        OtherMm = DistanceMm * Tangent(AngleValue.ValueSi)
    elif SecondValue is not None:
        OtherMm = SecondValue.ValueSi * 1000.0
    return PrismPlan(
        FrameValue,
        ChmfCutRing(EdgeValue, DistanceMm, OtherMm),
        Upper[Along] - Lower[Along],
        {
            "method": "typed_parametric_ordinary_chamfer",
            "feature_owner": NativeNodeSpan(LinkValue, Owners.FeatureValue),
            "stock_owner": NativeNodeSpan(LinkValue, Owners.StockValue),
            "selected_edge": NativeNodeSpan(LinkValue, Owners.SelectedRef),
            "native_kernel_identity": False,
        },
    )


# a chamfer modifies the existing stock body while its neutral geometry uses the same analytic prism builder
def BuildChmfGeom(PartValue: ChmfPartRead, BodyId: str) -> PartGeometry:
    Geometry = BuildPrismGeom(
        PartValue.PrismValue,
        BodyId,
        CreatorValue=PartValue.OwnersValue.FeatureValue,
    )
    Topology = Geometry.TopologyValue
    if (
        Topology.solid_count,
        Topology.shell_count,
        Topology.face_count,
        Topology.edge_count,
        Topology.vertex_count,
    ) != (1, 1, 7, 15, 10):
        raise ValueError("chamfer topology differs from the exact clipped stock")
    return ReplaceValue(Geometry, CreatorValue=None)
