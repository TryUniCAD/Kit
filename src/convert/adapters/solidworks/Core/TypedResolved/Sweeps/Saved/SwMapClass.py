from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the compatible readback must bind unambiguous class members in the actual archive map
def SwMapClass(MapValue: MapSnapshot, ClassName: str) -> tuple[ArchiveNode, ...]:
    return tuple(
        NodeValue
        for EntryValue in MapValue.EntriesValue
        if isinstance(NodeValue := EntryValue.EntryValue, ArchiveNode)
        and NodeValue.ClassValue.NameValue == ClassName
    )
