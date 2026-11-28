from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# legacy tree rows keep their order while typed owners supply concrete identity and serialized names
def BindFeature(
    Feature: NativeFeature, NodeValue: ArchiveNode, LinkValue: NativeLink
) -> NativeFeature:
    if Feature.object_id != NativeNodeId(NodeValue):
        raise ValueError("legacy feature identity differs from its typed owner")
    return ReplaceValue(
        Feature,
        name=ReadNativeName(NodeValue),
        class_name=NodeValue.ClassValue.NameValue,
        TypedOwner=NativeNodeSpan(LinkValue, NodeValue),
    )
