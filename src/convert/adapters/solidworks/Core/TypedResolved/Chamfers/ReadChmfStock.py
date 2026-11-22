from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckFirstBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import (
    ReadPrismLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from interchange.geometry.Models.Transform import Transform


# the selected solid must be the actual rectangular blind owner with its typed contour and depth
def ReadChmfStock(
    LinkValue: NativeLink,
    StockValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
) -> tuple[ExtrudeOwner, PrismPlan, LineLoop]:
    OwnerValue = ReadExtrude(LinkValue, StockValue, Features)
    CheckFirstBoss(OwnerValue)
    CheckPrismAtom(StockValue, HasColdOutput=True)
    CheckBossState(StockValue)
    CheckPrismEnd(OwnerValue)
    RootValue = LinkValue.ConfigValue.RootValue
    CheckPrismPlane(Features, RootValue)
    FrameValue = ReadPrismFrame(OwnerValue.ProfileValue, RootValue, Features)
    LoopValue = ReadPrismLoop(OwnerValue.ProfileValue, LinkValue)
    DepthValue = OwnerValue.RequireDepth().DepthValue.value_mm
    Points = set(
        PointValue.PositionValue for PointValue in LoopValue.PointsValue.values()
    )
    if (
        FrameValue != Transform()
        or DepthValue is None
        or DepthValue <= 0.0
        or LoopValue.DimsValue is not None
        or len(Points) != 4
        or len({PointValue[0] for PointValue in Points}) != 2
        or len({PointValue[1] for PointValue in Points}) != 2
    ):
        raise ValueError("chamfer requires the actual free rectangular Front stock")
    PrismValue = PrismPlan(
        FrameValue,
        MakePrismLines(LoopValue),
        DepthValue,
        {"stock_owner": NativeNodeSpan(LinkValue, StockValue)},
    )
    return OwnerValue, PrismValue, LoopValue
