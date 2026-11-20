from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.Geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorPlane import PlaneVector


# each regenerated body must own one closed valid solid and its independent analytic measures
def MakeColdSolid(
    BodyId: str,
    PlanValue: PrismPlan,
    ShapeValue: tuple[BrepModel, float, float, BoundingBox],
    CenterValue: PlaneVector,
) -> ColdSolid:
    BrepValue, Volume, AreaValue, Bounds = ShapeValue
    Center = PlacePrismPoint(
        PlanValue.FrameValue, CenterValue, PlanValue.DepthValue / 2
    )
    if (
        len(BrepValue.bodies) != 1
        or len(BrepValue.regions) != 1
        or len(BrepValue.shells) != 1
        or not BrepValue.regions[0].solid
        or not BrepValue.shells[0].closed
        or BrepValue.bodies[0].design_body_id != BodyId
        or not all(
            IsFinite(Value)
            for Value in (Volume, AreaValue, Center.x, Center.y, Center.z)
        )
        or min(Volume, AreaValue) <= 0
    ):
        raise ValueError(
            "cold model did not produce one measurable solid for its actual body"
        )
    BodyValue = ReplaceValue(BrepValue.bodies[0], id=f"{BodyId}:brep")
    return ColdSolid(
        ReplaceValue(BrepValue, bodies=(BodyValue,)), Volume, AreaValue, Bounds, Center
    )
