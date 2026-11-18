from math import isfinite as IsFinite, pi as PiValue

from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.BuildPocketShell import (
    BuildPocketShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismGeometry import (
    PrismGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordTopology import TopologyCounts


# clipped cylinder stations preserve exact cavity geometry independently of the presence of a driving cut distance
def BuildCircularCut(
    PlanValue: PrismPlan,
    CircleValue: LocalCircle,
    StockBounds: tuple[float, float],
    CutBounds: tuple[float, float],
    BodyId: str,
    PrefixValue: str,
) -> PrismGeometry:
    OpenCaps = tuple(
        IndexValue
        for IndexValue, (StockCap, ToolCap) in enumerate(
            zip(StockBounds, CutBounds, strict=True)
        )
        if StockCap == ToolCap
    )
    if not OpenCaps or not (
        StockBounds[0] <= CutBounds[0] < CutBounds[1] <= StockBounds[1]
    ):
        raise ValueError(
            "circular cut must intersect a cap and remain within the stock"
        )
    Stock, StockVolume, StockArea, Bounds = BuildPrism(
        BodyId, PlanValue.FrameValue, PlanValue.LinesValue, *StockBounds
    )
    Radius = CircleValue.RadiusValue
    ToolValue, ToolVolume, _, _ = BuildCircular(
        f"{BodyId}-cavity",
        PlanValue.FrameValue,
        CircleGeometry(PlaneVector(*CircleValue.CenterValue), Radius),
        *CutBounds,
        Radius,
        Radius,
    )
    ModelValue = BuildPocketShell(Stock, ToolValue, BodyId, PrefixValue, OpenCaps)
    Volume = StockVolume - ToolVolume
    Height = CutBounds[1] - CutBounds[0]
    Area = (
        StockArea
        + 2.0 * PiValue * Radius * Height
        + (2 - 2 * len(OpenCaps)) * PiValue * Radius**2
    )
    if not (IsFinite(Volume) and Volume > 0.0 and IsFinite(Area)):
        raise ValueError("cache free pocket measures exceed floating range")
    Topology = TopologyCounts(
        solid_count=len(ModelValue.bodies),
        shell_count=len(ModelValue.shells),
        face_count=len(ModelValue.faces),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
        volume=Volume,
        surface_area=Area,
        bounding_box=Bounds,
        valid=True,
    )
    return PrismGeometry(ModelValue, Topology, PlanValue.EvidenceValue)
