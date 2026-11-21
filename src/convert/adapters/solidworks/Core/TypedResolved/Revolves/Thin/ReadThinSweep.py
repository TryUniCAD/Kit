from collections.abc import Mapping
from math import pi as PiValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
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
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinLines import (
    ReadThinLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.CheckThinAxis import (
    CheckThinAxis,
)


# the thin boss must use its sole actual open sketch before considering the output body
def ReadThinParent(
    NodeValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> ArchiveNode:
    FieldsValue = NodeValue.FieldsValue
    ParentsValue = ReadParents(NodeValue)
    if (
        len(ParentsValue) != 1
        or ParentsValue[0].ClassValue.NameValue != "moProfileFeature_c"
        or Features.get(NativeNodeId(ParentsValue[0])) is not ParentsValue[0]
        or ParentsValue[0].FieldsValue.get("f3dc") != 0
        or ParentsValue[0].FieldsValue.get("pd_f110") is not None
        or tuple(
            FieldsValue.get(NameValue)
            for NameValue in ("f820", "f824", "f828", "f870", "f8e8")
        )
        != (0, 0, 5, 1, 0)
        or not IsLineState(FieldsValue.get("f818"))
    ):
        raise ValueError("SOLIDWORKS thin sweep requires its actual forward profile")
    return ParentsValue[0]


# distinct angular and axis writers share the already qualified principal support grammar
def ReadThinSweep(
    LinkValue: NativeLink, NodeValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> RevolveOwner:
    RootValue = LinkValue.ConfigValue.RootValue
    ProfileValue = ReadThinParent(NodeValue, Features)
    EndValue = ReadRevEnd(LinkValue, NodeValue.FieldsValue, False)
    if (
        EndValue.ModeValue != "one_sided"
        or EndValue.AlongValue.NameValue != "D1"
        or EndValue.AlongValue.RadiansValue >= PiValue
    ):
        raise ValueError("SOLIDWORKS thin sweep requires one positive partial D1")
    Reference = ReadRevAxisRef(NodeValue, ProfileValue, RootValue)
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    LinesValue = ReadThinLines(LinkValue, SketchValue, Reference)
    FrameValue = ReadRevFrame(ProfileValue, RootValue, Features, LinesValue, False)
    _ = ReadPrincAxis(FrameValue.SupportValue)
    CheckThinAxis(Reference, FrameValue)
    return RevolveOwner(
        NodeValue,
        ProfileValue,
        SketchValue,
        EndValue,
        Reference,
        LinesValue,
        FrameValue,
        False,
    )
