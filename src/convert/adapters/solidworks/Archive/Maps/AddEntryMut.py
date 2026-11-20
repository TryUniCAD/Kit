from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import KCounterLimit
from convert.adapters.solidworks.Archive.Maps.PutEntryMut import PutEntryMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# allocation must happen before body recursion can resolve self references
def AddEntryMut(MapValue: ArchiveMaps, EntryValue: RuntimeClass | ArchiveNode) -> int:
    if type(EntryValue) is not RuntimeClass:
        _ = ArchiveNode.RequireNode(EntryValue)
    if MapValue.CounterValue >= KCounterLimit:
        raise ValueError("archive map reached the native allocation limit")
    IndexValue = MapValue.CounterValue
    PutEntryMut(MapValue, MapEntry(IndexValue, EntryValue))
    MapValue.CounterValue += 1
    return IndexValue
