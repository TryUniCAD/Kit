from collections.abc import Iterable

from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import KCounterLimit
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# direct bindings inherit existing objects without serializing their class or body
def BindNodesMut(MapValue: ArchiveMaps, NodesValue: Iterable[ArchiveNode]) -> None:
    Nodes = tuple(ArchiveNode.RequireNode(NodeValue) for NodeValue in NodesValue)
    if MapValue.CounterValue + len(Nodes) > KCounterLimit:
        raise ValueError("direct archive objects exceed the native allocation limit")
    for NodeValue in Nodes:
        _ = AddEntryMut(MapValue, NodeValue)
    MapValue.BaseValue = MapValue.CounterValue
