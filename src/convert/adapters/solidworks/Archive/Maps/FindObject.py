from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ExternalRef import ExternalRef
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# only missing inherited slots can stand for external object references
def FindObject(MapValue: ArchiveMaps, IndexValue: int) -> ArchiveNode | ExternalRef:
    if type(IndexValue) is not int:
        raise TypeError("archive object index must be an integer")
    if not 1 <= IndexValue <= 0x7FFFFFFF:
        raise ValueError("archive object index exceeds the tag domain")
    EntryValue = MapValue.EntryMap.get(IndexValue)
    if EntryValue is None and IndexValue < MapValue.BaseValue:
        return ExternalRef(IndexValue)
    if EntryValue is None:
        raise ValueError(f"unresolved archive object reference {IndexValue}")
    if isinstance(EntryValue.EntryValue, (RuntimeClass, ExternalClass)):
        raise ValueError(f"wrong kind archive object reference {IndexValue}")
    return ArchiveNode.RequireNode(EntryValue.EntryValue)
