from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import (
    ChmfEdgePlan,
    KStockBounds,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector

# physical witness comparisons use the proven stock edge endpoint tolerance
KChmfPickTol = 1e-12


# both neutral selections must name the same prior feature and supply a real model space witness
def ReadChmfPoint(
    PickValue: Selection, BossValue: FeatureStep, RoleValue: str
) -> KDatumVector:
    PointValue = PickValue.point
    if (
        PickValue.path != (SelectPathElem("feature", BossValue.id, RoleValue),)
        or PickValue.name != BossValue.name + " " + RoleValue
        or type(PointValue) is not SpaceVector
        or PickValue.query
        or PickValue.provenance is not None
        or PickValue.attributes
    ):
        raise ValueError(
            "chamfer requires the actual prior edge and distance face picks"
        )
    return (
        RequireScalar(PointValue.x) / 1000.0,
        RequireScalar(PointValue.y) / 1000.0,
        RequireScalar(PointValue.z) / 1000.0,
    )


# each coordinate must meet one signed plane or lie strictly in the finite extent
def ChmfStation(CoordValue: float, BoundsValue: tuple[float, float]) -> int:
    Lower, Upper = BoundsValue
    if Upper - Lower <= 2 * KChmfPickTol:
        raise ValueError("chamfer stock extent is too small to distinguish its sides")
    if abs(CoordValue - Lower) <= KChmfPickTol:
        return 0
    if abs(CoordValue - Upper) <= KChmfPickTol:
        return 1
    if Lower < CoordValue < Upper:
        return -1
    raise ValueError("chamfer witness lies outside the actual finite stock")


# two boundary planes identify one physical edge while its chosen carrier determines the setback axis
def ReadChmfPicks(
    BoundsValue: KStockBounds,
    ShortSpan: float,
    BossValue: FeatureStep,
    PicksValue: tuple[Selection, Selection],
) -> ChmfEdgePlan:
    EdgePoint = ReadChmfPoint(PicksValue[0], BossValue, "edge")
    FacePoint = ReadChmfPoint(PicksValue[1], BossValue, "distance face")
    EdgeStations = tuple(
        ChmfStation(Coord, SpanValue)
        for Coord, SpanValue in zip(EdgePoint, BoundsValue, strict=True)
    )
    FaceStations = tuple(
        ChmfStation(Coord, SpanValue)
        for Coord, SpanValue in zip(FacePoint, BoundsValue, strict=True)
    )
    if EdgeStations.count(-1) != 1 or FaceStations.count(-1) != 2:
        raise ValueError("chamfer needs one edge interior and one face interior")
    EdgeAxis = EdgeStations.index(-1)
    DistanceAxis = next(
        Index for Index, Station in enumerate(FaceStations) if Station >= 0
    )
    if EdgeStations[DistanceAxis] != FaceStations[DistanceAxis]:
        raise ValueError("chamfer distance face must be incident to the selected edge")
    return ChmfEdgePlan(
        BoundsValue,
        EdgeAxis,
        DistanceAxis,
        CastValue(tuple[int, int, int], EdgeStations),
        ShortSpan,
    )
