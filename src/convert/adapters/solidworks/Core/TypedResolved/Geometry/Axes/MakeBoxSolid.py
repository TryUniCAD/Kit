from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisStock import (
    AxisStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import (
    BuildPrismGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan


# derived topology follows the checked section and live signed depth without a kernel cache
def MakeBoxSolid(
    StockValue: AxisStock, ColdValue: ColdOutput, AxesValue: PrismAxes, BodyId: str
) -> PartGeometry:
    OwnerValue = StockValue.OwnerValue
    Depth = OwnerValue.DepthValue.DepthValue
    if Depth.value_mm is None:
        raise ValueError("cache free box has no actual driving height")
    PlanValue = PrismPlan(
        StockValue.FrameValue,
        MakePrismLines(StockValue.LoopValue),
        Depth.value_mm,
        {
            "method": "typed_parametric_rectangular_prism",
            "profile_owner": NativeNodeSpan(
                ColdValue.LinkValue, OwnerValue.ProfileValue
            ),
            "boss_owner": NativeNodeSpan(ColdValue.LinkValue, OwnerValue.NodeValue),
            "depth_owner": Depth.TypedOwner,
        },
        ReversedBlind=True,
    )
    return ReplaceValue(
        BuildPrismGeom(PlanValue, BodyId, ColdValue, CreatorValue=ColdValue.BossValue),
        AxesValue=AxesValue,
    )
