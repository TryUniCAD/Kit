from collections import Counter

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqBoss import (
    CheckEqBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.HasNamedEq import (
    HasNamedEq,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqParams import (
    CheckEqParams,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqDormant import (
    ReadEqDormant,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqRef import ReadEqRef
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqTokens import (
    ReadEqTokens,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqWidth import (
    ReadEqWidth,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.WidthDepthLink import (
    WidthDepthLink,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import KTransformIdentity


# equation captions must identify one local sketch feature and exclude token separators
def ReadEqLabels(
    ProfileValue: ArchiveNode, BossValue: ArchiveNode, WidthParam: str, DepthParam: str
) -> tuple[str, str]:
    WidthName, DepthName = ReadNativeName(ProfileValue), ReadNativeName(BossValue)
    if WidthName == DepthName or any(
        Character in WidthName + DepthName for Character in ('"', "@")
    ):
        raise ValueError("local width-depth equation has ambiguous dimension names")
    return f'"{WidthParam}@{WidthName}"', f'"{DepthParam}@{DepthName}"'


# the scoped expression needs the actual projected sketch and live blind depth before public parameters can be bound
def ReadWidthDepth(
    Model: NativeModel, LinkValue: NativeLink, SourceValue: SldprtArchive
) -> WidthDepthLink:
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    FeatureNodes = IndexFeatures(LinkValue)
    Expected = {
        **dict.fromkeys(
            KSystemFolders
            | {
                "moDetailCabinet_c",
                "moOriginProfileFeature_c",
                "moProfileFeature_c",
                "moExtrusion_c",
            },
            1,
        ),
        "moRefPlane_c": 3,
    }
    if (
        Counter(NodeValue.ClassValue.NameValue for NodeValue in FeatureNodes.values())
        != Expected
    ):
        raise ValueError(
            "local width-depth equation requires one ordinary part history"
        )
    (Sketch,) = Model.sketches
    (Operation,) = Model.operations
    BossValue = ReadExtrude(LinkValue, FeatureNodes[Operation.object_id], FeatureNodes)
    CheckEqBoss(BossValue)
    if (
        BossValue.ProfileValue is not FeatureNodes[Sketch.object_id]
        or ReadPrismFrame(BossValue.ProfileValue, RootValue, FeatureNodes)
        != KTransformIdentity
    ):
        raise ValueError("local width-depth equation requires the actual Front support")
    WidthValue, HeightValue = ReadEqWidth(Sketch.TypedLines)
    DepthValue = BossValue.RequireDepth()
    WidthParam, DepthParam = WidthValue.NameValue, DepthValue.DepthValue.name
    HasNamedLabels = HasNamedEq(
        (WidthParam, HeightValue.NameValue, DepthParam), SourceValue
    )
    MetresValue = DepthValue.DepthValue.native_value
    if (
        MetresValue is None
        or WidthValue.ParamValue.FieldsValue.get("f58") != WidthValue.MetresValue
        or MetresValue != WidthValue.MetresValue / 2
    ):
        raise ValueError("local width-depth equation disagrees with live depth")
    CheckEqParams(
        Model,
        Sketch.object_id,
        Operation.object_id,
        WidthValue,
        DepthValue,
        HeightValue=HeightValue if HasNamedLabels else None,
    )
    WidthText, DepthText = ReadEqLabels(
        BossValue.ProfileValue, BossValue.NodeValue, WidthParam, DepthParam
    )
    Relation, DepthToken, WidthToken, RelationNodes = ReadEqTokens(
        RootValue, DepthText, WidthText
    )
    WidthComp, WidthOwner = ReadEqRef(
        LinkValue, WidthToken, WidthValue.HandleValue, WidthValue.MetresValue
    )
    DepthComp, DepthOwner = ReadEqRef(
        LinkValue, DepthToken, DepthValue.HandleValue, MetresValue
    )
    if WidthComp is DepthComp:
        raise ValueError("local equation dimension clones share a component owner")
    RightText = f"{WidthText} / 2"
    return WidthDepthLink(
        SourceValue,
        LinkValue,
        f"{DepthText} = {RightText}",
        RightText,
        Sketch.object_id,
        Operation.object_id,
        NativeNodeSpan(LinkValue, Relation),
        WidthOwner,
        DepthOwner,
        RelationNodes,
        WidthParam,
        DepthParam,
        (
            ReadEqDormant(LinkValue, BossValue, (WidthValue, HeightValue))
            if HasNamedLabels
            else None
        ),
    )
