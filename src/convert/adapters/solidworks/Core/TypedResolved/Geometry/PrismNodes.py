from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import (
    KPrismClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# all allocated native owners must be inspected so detached or extra geometry cannot hide behind the visible feature roots
def PrismNodes(
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    ColdAtom: ArchiveNode | None = None,
    *,
    AllowedClasses: frozenset[str] = KPrismClasses,
    ProvenNodes: frozenset[ArchiveNode] = frozenset(),
) -> tuple[ArchiveNode, ...]:
    Entries = (
        *LinkValue.ResolvedValue.MapValue.EntriesValue,
        *ManagerValue.MapValue.EntriesValue,
    )
    NodesValue = tuple(
        Entry.EntryValue
        for Entry in Entries
        if isinstance(Entry.EntryValue, ArchiveNode)
    )
    FoundNodes: set[ArchiveNode] = set()
    for NodeValue in NodesValue:
        _ = RequireNative(NodeValue)
        if (
            NodeValue.ClassValue.NameValue not in AllowedClasses
            and NodeValue is not ColdAtom
        ):
            if NodeValue not in ProvenNodes or NodeValue in FoundNodes:
                raise ValueError("cache free prism has an unsupported native owner")
            FoundNodes.add(NodeValue)
    if FoundNodes != ProvenNodes or (
        ProvenNodes
        and not ProvenNodes.issubset(
            EntryValue.EntryValue
            for EntryValue in LinkValue.ConfigValue.MapValue.EntriesValue
        )
    ):
        raise ValueError("cache free prism lacks its exact linked relation inventory")
    return NodesValue
