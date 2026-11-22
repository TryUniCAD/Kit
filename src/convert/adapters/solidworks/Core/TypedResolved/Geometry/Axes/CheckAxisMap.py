from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink

# these classes are exclusive to the additional typed axis subgraphs in the ordinary box
KAxisClasses = frozenset(("moRefAxis_c", "moPlaneInterAxisData_c", "moPlaneRef_w"))


# only the exact new vertices proved on the same linked map may leave the prism inventory
def CheckAxisMap(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    NodesValue: tuple[ArchiveNode, ...],
    AxesValue: PrismAxes,
) -> tuple[dict[int, ArchiveNode], tuple[ArchiveNode, ...]]:
    Members = AxesValue.MembersValue
    if (
        AxesValue.LinkValue is not LinkValue
        or sum(NodeValue in Members for NodeValue in NodesValue) != len(Members)
        or not Members.issubset(NodesValue)
        or any(
            NodeValue.ClassValue.NameValue in KAxisClasses and NodeValue not in Members
            for NodeValue in NodesValue
        )
        or any(
            isinstance(Entry.EntryValue, ArchiveNode) and Entry.EntryValue in Members
            for Entry in LinkValue.ConfigValue.MapValue.EntriesValue
        )
    ):
        raise ValueError(
            "cache free origin axis map contains detached or foreign owners"
        )
    return (
        {
            KeyValue: NodeValue
            for KeyValue, NodeValue in Features.items()
            if NodeValue not in Members
        },
        tuple(NodeValue for NodeValue in NodesValue if NodeValue not in Members),
    )
