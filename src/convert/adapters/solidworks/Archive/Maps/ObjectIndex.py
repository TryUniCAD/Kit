from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# equal field payloads must never merge distinct native objects
def ObjectIndex(MapValue: ArchiveMaps, NodeValue: ArchiveNode) -> int | None:
    _ = ArchiveNode.RequireNode(NodeValue)
    return MapValue.ObjectLookup.get(id(NodeValue))
