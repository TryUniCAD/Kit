from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps


# a rejected untagged body cannot allocate or replace entries in the enclosing map
def CopyOwnedMap(MapValue: ArchiveMaps) -> ArchiveMaps:
    Snapshot = MapValue.Snapshot()
    LocalMap = ArchiveMaps(Snapshot.CounterValue, Snapshot)
    LocalMap.BaseValue = MapValue.BaseValue
    return LocalMap
