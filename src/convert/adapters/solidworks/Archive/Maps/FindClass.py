from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# unresolved class slots need explicit context instead of inferred feature names
def FindClass(MapValue: ArchiveMaps, IndexValue: int) -> RuntimeClass | ExternalClass:
    if type(IndexValue) is not int:
        raise TypeError("archive class index must be an integer")
    if not 1 <= IndexValue <= 0x7FFFFFFF:
        raise ValueError("archive class index exceeds the tag domain")
    EntryValue = MapValue.EntryMap.get(IndexValue)
    if EntryValue is None or not isinstance(
        EntryValue.EntryValue, (RuntimeClass, ExternalClass)
    ):
        raise ValueError(
            f"unresolved or wrong kind archive class reference {IndexValue}"
        )
    return EntryValue.EntryValue
