from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdBoxCenter import (
    ColdBoxCenter,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.MakeColdSolid import (
    MakeColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism


# the retained uncut body must remain the exact independent blind prism
def BuildColdBox(PlanValue: PrismPlan, BodyId: str) -> ColdSolid:
    ShapeValue = BuildPrism(
        BodyId, PlanValue.FrameValue, PlanValue.LinesValue, 0.0, PlanValue.DepthValue
    )
    return MakeColdSolid(BodyId, PlanValue, ShapeValue, ColdBoxCenter(PlanValue))
