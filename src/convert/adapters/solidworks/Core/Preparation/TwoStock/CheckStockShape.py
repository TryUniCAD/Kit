from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockPrism import (
    MakeStockPrism,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BuildColdBox import (
    BuildColdBox,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BuildColdCut import (
    BuildColdCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.CheckStockGap import (
    CheckStockGap,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.JoinColdGeom import (
    JoinColdGeom,
)
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# admitted cutters must produce two valid disjoint modeled solids before any native bytes are made
def CheckStockShape(PlanValue: TwoStockPlan) -> None:
    FrontStock, RightStock = PlanValue.StockValues
    FrontPlan = MakeStockPrism(FrontStock)
    Original = BuildColdBox(FrontPlan, FrontStock.BodyId)
    Untouched = BuildColdBox(MakeStockPrism(RightStock), RightStock.BodyId)
    CheckStockGap(Original.BoundsValue, Untouched.BoundsValue)
    Circle = PlanValue.CircleValue
    ToolValue = CircleGeometry(
        PlaneVector(*(Coordinate * 1000.0 for Coordinate in Circle.CenterValue)),
        Circle.RadiusValue * 1000.0,
    )
    ResultValue = BuildColdCut(FrontPlan, ToolValue, PlanValue.ResultBodyId, Original)
    _ = JoinColdGeom(
        Untouched, ResultValue, frozenset((RightStock.BodyId, PlanValue.ResultBodyId))
    )
