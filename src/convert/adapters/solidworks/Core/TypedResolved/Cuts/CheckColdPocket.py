from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckColdCutRoots import (
    CheckColdRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckPrismBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import (
    ReadPrismLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# a cold all bodies cut can infer its producer only when exact local geometry proves the sole intersection
def CheckColdPocket(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    BossValue: ExtrudeOwner,
    CutValue: ExtrudeOwner,
    SelectedStock: ArchiveNode | None = None,
) -> None:
    RootValue = LinkValue.ConfigValue.RootValue
    CheckColdRoots(Features)
    CheckPrismRoot(RootValue, SelectedStock)
    CheckPrismRels(RootValue)
    Through = CutValue.ModeValue == ExtrudeEnd.KThroughAll
    CheckPrismBoss(
        BossValue,
        ModeValue=ExtrudeEnd.KMidPlane if Through else ExtrudeEnd.KBlind,
        SelectedStock=SelectedStock is not None,
    )
    CheckPrismEnd(BossValue)
    CheckPrismAtom(
        CutValue.NodeValue, SelectedScope="cut" if SelectedStock is not None else None
    )
    CheckPrismProf(CutValue.ProfileValue)
    BossFrame = ReadPrismFrame(
        BossValue.ProfileValue, RootValue, Features, FrontOnly=not Through
    )
    CutFrame = ReadPrismFrame(
        CutValue.ProfileValue, RootValue, Features, FrontOnly=not Through
    )
    if BossFrame != CutFrame:
        raise ValueError("cold cut requires one exact shared datum")
    Lines = MakePrismLines(ReadPrismLoop(BossValue.ProfileValue, LinkValue))
    Circle = RequireNative(CutValue.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Shape = ReadLocalCirc(Circle, LinkValue, AllowFree=True)
    if Shape is None:
        raise ValueError("cold blind cut requires a single actual closed circle")
    CircleValue, _ = Shape
    XValue, YValue = CircleValue.CenterValue
    Radius = CircleValue.RadiusValue
    XValues = tuple(LineValue.start.x for LineValue in Lines)
    YValues = tuple(LineValue.start.y for LineValue in Lines)
    if not min(XValues) < XValue - Radius < XValue + Radius < max(XValues) or not min(
        YValues
    ) < YValue - Radius < YValue + Radius < max(YValues):
        raise ValueError(
            "cold circular cut must stay inside the actual rectangular sides"
        )
    if not Through and not (
        0.0
        < CutValue.RequireDepth().DepthValue.value_mm
        < BossValue.RequireDepth().DepthValue.value_mm
    ):
        raise ValueError("cold blind pocket must terminate inside its stock")
