from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# canonical class references must reuse the descriptor already owned by this map
def ClassIndex(
    MapValue: ArchiveMaps, ClassValue: RuntimeClass | ExternalClass
) -> int | None:
    if type(ClassValue) not in (RuntimeClass, ExternalClass):
        raise TypeError("archive class lookup requires a typed descriptor")
    return MapValue.ClassLookup.get(ClassValue)
