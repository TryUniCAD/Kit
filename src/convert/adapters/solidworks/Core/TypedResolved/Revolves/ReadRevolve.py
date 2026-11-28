from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevProfile import (
    ReadRevProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAngle import (
    ReadRevAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAxisRef import (
    ReadRevAxisRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevFrame import (
    ReadRevFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# only the witnessed ordinary linked feature may replace its legacy semantic fallback
def ReadRevolve(
    LinkValue: NativeLink, NodeValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> RevolveOwner:
    NodeValue = RequireNative(NodeValue, "moRevolution_c")
    if Features.get(NativeNodeId(NodeValue)) is not NodeValue:
        raise ValueError("ordinary revolve does not alias its resolved feature root")
    RootValue = RequireNative(FindModelRoot(LinkValue.ConfigValue.MapValue), "moPart_c")
    ParentsValue = ReadParents(NodeValue)
    if (
        len(ParentsValue) != 1
        or ParentsValue[0].ClassValue.NameValue != "moProfileFeature_c"
        or (Features.get(NativeNodeId(ParentsValue[0])) is not ParentsValue[0])
    ):
        raise ValueError("ordinary revolve requires its actual sole profile dependency")
    ProfileValue = ParentsValue[0]
    if (
        ProfileValue.FieldsValue.get("f3dc") != 0
        or ProfileValue.FieldsValue.get("pd_f110") is not None
    ):
        raise ValueError(
            "ordinary revolve profile branch is outside measured semantics"
        )
    FieldsValue = NodeValue.FieldsValue
    ReverseValue = FieldsValue.get("f824")
    if (
        FieldsValue.get("f820") != 0
        or type(ReverseValue) is not int
        or ReverseValue not in (0, 1)
        or (
            FieldsValue.get("f828") != 3
            or FieldsValue.get("f870") != 1
            or FieldsValue.get("f8e8") != 0
            or not IsLineState(FieldsValue.get("f818"))
        )
    ):
        raise ValueError(
            "ordinary revolve direction type or converted sketch state is unqualified"
        )
    AngleValue = ReadRevAngle(LinkValue, NodeValue)
    AxisValue = ReadRevAxisRef(NodeValue, ProfileValue, RootValue)
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    ProfileGraph = ReadRevProfile(SketchValue, AxisValue, LinkValue)
    FrameValue = ReadRevFrame(
        ProfileValue, RootValue, Features, ProfileGraph, bool(ReverseValue)
    )
    return RevolveOwner(
        NodeValue,
        ProfileValue,
        SketchValue,
        AngleValue,
        AxisValue,
        ProfileGraph,
        FrameValue,
        bool(ReverseValue),
    )
