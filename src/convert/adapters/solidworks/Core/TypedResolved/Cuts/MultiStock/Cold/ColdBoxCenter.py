from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.geometry.Models.VectorPlane import PlaneVector


# opposite validated rectangle corners give the exact uncut planar centroid
def ColdBoxCenter(PlanValue: PrismPlan) -> PlaneVector:
    FirstValue = PlanValue.LinesValue[0].start
    LastValue = PlanValue.LinesValue[2].start
    return PlaneVector(
        (FirstValue.x + LastValue.x) / 2, (FirstValue.y + LastValue.y) / 2
    )
