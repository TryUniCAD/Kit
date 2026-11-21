from collections.abc import Mapping
from typing import Literal

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevProfile import (
    ReadRevProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAxisRef import (
    ReadRevAxisRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevEnd import (
    ReadRevEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevFrame import (
    ReadRevFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# a qualified operation and its actual profile use the same live axis and end grammar
def ReadRevCore(
    LinkValue: NativeLink,
    NodeValue: ArchiveNode,
    ProfileValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    MergeCode: Literal[0, 1],
) -> RevolveOwner:
    RootValue = RequireNative(FindModelRoot(LinkValue.ConfigValue.MapValue), "moPart_c")
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
        or FieldsValue.get("f828") != 3
        or FieldsValue.get("f870") != MergeCode
        or FieldsValue.get("f8e8") != 0
        or not IsLineState(FieldsValue.get("f818"))
    ):
        raise ValueError(
            "ordinary revolve direction type or converted sketch state is unqualified"
        )
    EndValue = ReadRevEnd(LinkValue, FieldsValue, bool(ReverseValue))
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
        EndValue,
        AxisValue,
        ProfileGraph,
        FrameValue,
        bool(ReverseValue),
    )
