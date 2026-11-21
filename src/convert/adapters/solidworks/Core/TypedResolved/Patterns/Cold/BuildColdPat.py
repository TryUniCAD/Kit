from math import fsum as SumFloats, isclose as IsClose

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Extrude.Raised.JoinRaised import JoinRaised
from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.RaisedRims import (
    RaisedRims,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from interchange.Records.RecordTopology import TopologyCounts
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# the joined boundary consumes only independently positioned rectangles and their typed driving values
def BuildColdPat(
    LinkValue: NativeLink,
    OwnerValue: PatternOwner,
    StockPlans: tuple[PrismPlan, PrismPlan],
    BodyId: str,
) -> PartGeometry:
    PlateValue, SeedValue = StockPlans
    RimsValue = RaisedRims(PlateValue, SeedValue, OwnerValue)
    Plate, PlateVolume, PlateArea, PlateBounds = BuildPrism(
        BodyId, PlateValue.FrameValue, PlateValue.LinesValue, 0.0, PlateValue.DepthValue
    )
    Pieces = tuple(
        BuildPrism(
            f"{BodyId}-raised-{Index}",
            PlateValue.FrameValue,
            RimValue,
            PlateValue.DepthValue,
            SeedValue.DepthValue,
        )
        for Index, RimValue in enumerate(RimsValue)
    )
    Boundary = JoinRaised(BodyId, Plate, tuple(Value[0] for Value in Pieces))
    Bounds = BoundingBox(
        PlateBounds.minimum,
        SpaceVector(PlateBounds.maximum.x, PlateBounds.maximum.y, SeedValue.DepthValue),
    )
    DepthRise = SeedValue.DepthValue - PlateValue.DepthValue
    Volume = SumFloats((PlateVolume, *(Value[1] for Value in Pieces)))
    AreaValue = SumFloats(
        (PlateArea, *(Value[2] - 2 * Value[1] / DepthRise for Value in Pieces))
    )
    MassValue = ReadPartMass(Boundary, Bounds)
    if MassValue is None or not IsClose(Volume, MassValue.Volume, rel_tol=1e-12):
        raise ValueError(
            "constructed raised pattern boundary has inconsistent signed volume"
        )
    return PartGeometry(
        Boundary,
        TopologyCounts(
            solid_count=1,
            shell_count=1,
            face_count=len(Boundary.faces),
            edge_count=len(Boundary.edges),
            vertex_count=len(Boundary.vertices),
            volume=Volume,
            surface_area=AreaValue,
            bounding_box=Bounds,
            valid=True,
        ),
        {
            "method": "typed_parametric_contained_raised_pattern",
            "native_kernel_identity": False,
            "pattern_owner": NativeNodeSpan(LinkValue, OwnerValue.NodeValue),
            "centroid_mm": MassValue.Centroid,
        },
        ProducerValue=OwnerValue.NodeValue,
    )
