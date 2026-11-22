from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# copied field owners cannot inherit the authority of an actual linked archive object
def CheckTreeAlias(LinkValue: NativeLink, NodesValue: tuple[ArchiveNode, ...]) -> None:
    EntriesValue = LinkValue.ResolvedValue.MapValue.EntriesValue
    if any(
        NodeValue.IndexValue is None
        or not any(
            EntryValue.IndexValue == NodeValue.IndexValue
            and EntryValue.EntryValue is NodeValue
            for EntryValue in EntriesValue
        )
        for NodeValue in NodesValue
    ):
        raise ValueError(
            "through-all presentation owner does not alias its archive map"
        )
