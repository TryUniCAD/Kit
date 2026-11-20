from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a tagged suffix owner must belong to the current record rather than an earlier slot
def RequireMatNode(
    NodeValue: object, MapValue: ArchiveMaps, ClassValue: RuntimeClass, FirstSlot: int
) -> ArchiveNode:
    if not isinstance(NodeValue, ArchiveNode) or NodeValue.ClassValue != ClassValue:
        raise BodyUnsupported(
            f"SOLIDWORKS part material requires {ClassValue.NameValue}"
        )
    SlotValue = ObjectIndex(MapValue, NodeValue)
    if SlotValue is None or SlotValue < FirstSlot:
        raise BodyUnsupported("SOLIDWORKS part material requires newly read owners")
    return NodeValue
