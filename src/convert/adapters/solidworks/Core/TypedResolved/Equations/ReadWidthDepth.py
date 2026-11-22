from collections import Counter

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqParams import (
    CheckEqParams,
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
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the scoped expression needs the actual projected sketch and live blind depth before public parameters can be bound
def ReadWidthDepth(
    Model: NativeModel, LinkValue: NativeLink, BossValue: ExtrudeOwner
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
    WidthValue = ReadEqWidth(Sketch.TypedLines)
    DepthValue = BossValue.DepthValue
    MetresValue = DepthValue.DepthValue.native_value
    if (
        DepthValue.DepthValue.name != "D1"
        or MetresValue is None
        or WidthValue.ParamValue.FieldsValue.get("f58") != WidthValue.MetresValue
        or MetresValue != WidthValue.MetresValue / 2
    ):
        raise ValueError("local width-depth equation disagrees with live depth")
    CheckEqParams(Model, Sketch.object_id, Operation.object_id, WidthValue, DepthValue)
    WidthName = ReadNativeName(BossValue.ProfileValue)
    DepthName = ReadNativeName(BossValue.NodeValue)
    if Sketch.name != WidthName or Operation.name != DepthName:
        raise ValueError(
            "local equation names differ from the actual archived feature owners"
        )
    if WidthName == DepthName or any(
        Character in WidthName + DepthName for Character in ('"', "@")
    ):
        raise ValueError("local width-depth equation has ambiguous dimension names")
    WidthText, DepthText = f'"D1@{WidthName}"', f'"D1@{DepthName}"'
    Relation, DepthToken, WidthToken = ReadEqTokens(RootValue, DepthText, WidthText)
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
        f"{DepthText} = {RightText}",
        RightText,
        Sketch.object_id,
        Operation.object_id,
        NativeNodeSpan(LinkValue, Relation),
        WidthOwner,
        DepthOwner,
    )
