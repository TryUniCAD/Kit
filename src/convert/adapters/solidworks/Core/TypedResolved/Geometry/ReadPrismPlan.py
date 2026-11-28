from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckPrismBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import (
    ReadPrismLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.VectorSpace import SpaceVector


# only actual linked feature and dimension owners may determine the reconstructed body and its provenance
def ReadPrismBody(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    ColdValue: ColdOutput | None = None,
    *,
    ModeValue: ExtrudeEnd = ExtrudeEnd.KBlind,
    SelectedStock: bool = False,
    AllowFirstScope: bool = False,
    AllowPolygon: bool = False,
    DormantValue: DepthOwner | None = None,
) -> PrismPlan:
    (BossValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    OwnerValue = ReadExtrude(LinkValue, BossValue, Features)
    CheckPrismBoss(
        OwnerValue,
        ColdValue,
        ModeValue=ModeValue,
        SelectedStock=SelectedStock,
        AllowFirstScope=AllowFirstScope,
    )
    ReversedBlind = (
        OwnerValue.IsReversed
        and OwnerValue.ModeValue == ModeValue == ExtrudeEnd.KBlind
        and not SelectedStock
    )
    CheckPrismEnd(
        OwnerValue,
        ReversedBlind=ReversedBlind,
        SelectedMidPlane=SelectedStock and ModeValue == ExtrudeEnd.KMidPlane,
        DormantValue=DormantValue,
    )
    Depth = OwnerValue.RequireDepth().DepthValue
    Length = Depth.value_mm
    if Length is None:
        raise ValueError("cache free prism requires a measured active depth")
    PlainPolygon = (
        AllowPolygon
        and not SelectedStock
        and not ReversedBlind
        and ModeValue == ExtrudeEnd.KBlind
        and ColdValue is None
    )
    LoopValue = ReadPrismLoop(
        OwnerValue.ProfileValue, LinkValue, AllowPolygon=PlainPolygon
    )
    FrameValue = ReadPrismFrame(
        OwnerValue.ProfileValue,
        LinkValue.ConfigValue.RootValue,
        Features,
        FrontOnly=ModeValue == ExtrudeEnd.KBlind and not ReversedBlind,
    )
    if ReversedBlind and FrameValue.z_axis != SpaceVector(0.0, 1.0, 0.0):
        raise ValueError("cache free reversed prism requires its actual top support")
    EvidenceValue = {
        "method": "typed_parametric_rectangular_prism",
        "model_version": 19000,
        "profile_owner": NativeNodeSpan(LinkValue, OwnerValue.ProfileValue),
        "boss_owner": NativeNodeSpan(LinkValue, BossValue),
        "depth_owner": Depth.TypedOwner,
        "native_kernel_identity": False,
    }
    return PrismPlan(
        FrameValue,
        MakePrismLines(
            LoopValue,
            RequireRectangle=not (PlainPolygon and LoopValue.DimsValue is None),
        ),
        Length,
        EvidenceValue,
        ReversedBlind=ReversedBlind,
    )


# ordinary prism readers must confirm the standard untouched plane presentation
def ReadPrismPlan(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    ColdValue: ColdOutput | None = None,
    *,
    ModeValue: ExtrudeEnd = ExtrudeEnd.KBlind,
    SelectedStock: bool = False,
    AllowFirstScope: bool = False,
    AllowPolygon: bool = False,
    DormantValue: DepthOwner | None = None,
) -> PrismPlan:
    PlanValue = ReadPrismBody(
        LinkValue,
        Features,
        ColdValue,
        ModeValue=ModeValue,
        SelectedStock=SelectedStock,
        AllowFirstScope=AllowFirstScope,
        AllowPolygon=AllowPolygon,
        DormantValue=DormantValue,
    )
    CheckPrismPlane(Features, LinkValue.ConfigValue.RootValue)
    return PlanValue
