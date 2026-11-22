from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# detached objects with the same fields cannot replace the recorded material owners
def CheckMatSlots(MapValue: MapSnapshot, *NodesValue: ArchiveNode) -> None:
    SlotsValue = {
        EntryValue.IndexValue: EntryValue.EntryValue
        for EntryValue in MapValue.EntriesValue
    }
    for NodeValue in NodesValue:
        if (
            NodeValue.IndexValue is None
            or SlotsValue.get(NodeValue.IndexValue) is not NodeValue
        ):
            raise BodyUnsupported(
                "SOLIDWORKS assigned material owner is detached from its archive map"
            )
