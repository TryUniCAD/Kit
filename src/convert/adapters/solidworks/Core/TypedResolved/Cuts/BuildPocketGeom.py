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


# the validated pocket subtracts actual circular volume and adds the analytic wall without creating a native cache
def BuildPocketGeom(
    PlanValue: PrismPlan, CircleValue: LocalCircle, CutDepth: float, BodyId: str
) -> PrismGeometry:
    Stock, StockVolume, StockArea, Bounds = BuildPrism(
        BodyId, PlanValue.FrameValue, PlanValue.LinesValue, 0.0, PlanValue.DepthValue
    )
    Radius = CircleValue.RadiusValue
    ToolValue, ToolVolume, _, _ = BuildCircular(
        f"{BodyId}-cavity",
        PlanValue.FrameValue,
        CircleGeometry(PlaneVector(*CircleValue.CenterValue), Radius),
        0.0,
        CutDepth,
        Radius,
        Radius,
    )
    ModelValue = BuildPocketShell(Stock, ToolValue, BodyId)
    Volume = StockVolume - ToolVolume
    Area = StockArea + 2.0 * PiValue * Radius * CutDepth
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
