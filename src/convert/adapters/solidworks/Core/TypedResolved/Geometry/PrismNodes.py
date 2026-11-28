from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# provenance covers all allocated objects so detached geometry cannot hide behind visible feature roots
def PrismNodes(
    LinkValue: NativeLink, ManagerValue: CmgrGraph, AllowedClasses: frozenset[str]
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
    for NodeValue in NodesValue:
        _ = RequireNative(NodeValue)
        if NodeValue.ClassValue.NameValue not in AllowedClasses:
            raise ValueError("cache free prism has an unsupported native owner")
    return NodesValue
