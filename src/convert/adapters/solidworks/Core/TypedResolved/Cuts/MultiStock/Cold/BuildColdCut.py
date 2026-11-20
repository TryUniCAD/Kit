from math import isclose as IsClose, pi as PiValue

from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.BuildCircularCut import (
    BuildCircleCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BuildNotchRing import (
    BuildNotchRing,
)
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
from convert.Geometry.Extrude.Trimmed.TrimPrism import BuildTrimPrism
from interchange.geometry.Models.VectorPlane import PlaneVector


# the selected solid alone receives the exact through cut and removed section moment
def BuildColdCut(
    PlanValue: PrismPlan, CircleValue: LocalCircle, BodyId: str, Original: ColdSolid
) -> ColdSolid:
    CenterValue = PlaneVector(*CircleValue.CenterValue)
    Radius = CircleValue.RadiusValue
    First, LastValue = PlanValue.LinesValue[0].start, PlanValue.LinesValue[2].start
    DepthValue = PlanValue.DepthValue
    if (
        First.x < CenterValue.x - Radius < CenterValue.x + Radius < LastValue.x
        and First.y < CenterValue.y - Radius < CenterValue.y + Radius < LastValue.y
    ):
        SpanValue = (0.0, DepthValue)
        ResultValue = BuildCircleCut(
            PlanValue, CircleValue, SpanValue, SpanValue, BodyId, f"{BodyId}-through"
        )
        Topology = ResultValue.TopologyValue
        if (
            Topology.volume is None
            or Topology.surface_area is None
            or Topology.bounding_box is None
        ):
            raise ValueError("through cylinder lacks its analytic measures")
        ShapeValue = (
            ResultValue.BrepValue,
            Topology.volume,
            Topology.surface_area,
            Topology.bounding_box,
        )
        LossValue, Removed = PiValue * Radius**2, CenterValue
    else:
        RingValue, LossValue, Removed = BuildNotchRing(
            PlanValue.LinesValue, CenterValue, Radius
        )
        ShapeValue = BuildTrimPrism(
            BodyId, PlanValue.FrameValue, RingValue, 0.0, DepthValue
        )
    Remaining = Original.VolumeValue / DepthValue - LossValue
    if Remaining <= 0.0 or not IsClose(
        ShapeValue[1], Remaining * DepthValue, rel_tol=1e-10, abs_tol=1e-9
    ):
        raise ValueError(
            "computed cut material does not match its analytic removed section"
        )
    Intact = ColdBoxCenter(PlanValue)
    Ratio = LossValue / Remaining
    Center = PlaneVector(
        Intact.x + Ratio * (Intact.x - Removed.x),
        Intact.y + Ratio * (Intact.y - Removed.y),
    )
    return MakeColdSolid(BodyId, PlanValue, ShapeValue, Center)
