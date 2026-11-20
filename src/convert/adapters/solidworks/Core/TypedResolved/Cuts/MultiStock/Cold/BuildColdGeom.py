from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
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
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockBody import (
    ColdStockBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockPart import (
    ColdStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.JoinColdGeom import (
    JoinColdGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdPrism import (
    ReadColdPrism,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# reconstruction may cut only the validated earlier stock while leaving the independent solid intact
def BuildColdGeom(OwnersValue: ColdStockOwners) -> ColdStockPart:
    LinkValue = OwnersValue.LinkValue
    PlansValue = tuple(
        ReadColdPrism(OwnerValue, FrameValue, LinkValue)
        for OwnerValue, FrameValue in zip(
            OwnersValue.StockValues, OwnersValue.ProfileFrames[:2], strict=True
        )
    )
    CutValue = OwnersValue.CutValue
    SketchValue = RequireNative(
        CutValue.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch"
    )
    ToolValue = ReadLocalCirc(SketchValue, LinkValue, AllowFree=True)
    if ToolValue is None or ToolValue[1] is not None:
        raise ValueError("the cold cut requires its sole free circular profile")
    Circle = ToolValue[0]
    if (
        Circle.ModeValue is not None
        or Circle.DriverName is not None
        or not all(
            IsFinite(Value) for Value in (*Circle.CenterValue, Circle.RadiusValue)
        )
        or Circle.RadiusValue <= 0.0
    ):
        raise ValueError("the cold cut requires one positive finite free circle")
    Selected = OwnersValue.SelectedIndex
    StockNode = OwnersValue.StockValues[Selected].NodeValue
    OtherNode = OwnersValue.StockValues[1 - Selected].NodeValue
    PlanValue = PlansValue[Selected]
    Original = BuildColdBox(
        PlanValue, f"sldprt:feature:{NativeNodeId(StockNode)}:historical-stock"
    )
    Untouched = BuildColdBox(
        PlansValue[1 - Selected], f"sldprt:body:{NativeNodeId(OtherNode)}"
    )
    CheckStockGap(Original.BoundsValue, Untouched.BoundsValue)
    ResultValue = BuildColdCut(
        PlanValue, Circle, f"sldprt:body:{NativeNodeId(CutValue.NodeValue)}", Original
    )
    BodyValues = (
        ColdStockBody(OtherNode, Untouched),
        ColdStockBody(CutValue.NodeValue, ResultValue),
    )
    return ColdStockPart(
        OwnersValue,
        JoinColdGeom(
            Untouched, ResultValue, frozenset(Value.id for Value in BodyValues)
        ),
        BodyValues,
    )
