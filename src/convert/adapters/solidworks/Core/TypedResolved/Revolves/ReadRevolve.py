from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevCore import (
    ReadRevCore,
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
    ParentsValue = ReadParents(NodeValue)
    if (
        len(ParentsValue) != 1
        or ParentsValue[0].ClassValue.NameValue != "moProfileFeature_c"
        or (Features.get(NativeNodeId(ParentsValue[0])) is not ParentsValue[0])
    ):
        raise ValueError("ordinary revolve requires its actual sole profile dependency")
    return ReadRevCore(LinkValue, NodeValue, ParentsValue[0], Features, 1)
