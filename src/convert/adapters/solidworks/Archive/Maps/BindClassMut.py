from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.PutEntryMut import PutEntryMut
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass


# caller supplied prefix bindings resolve existing classes without consuming new slots
def BindClassMut(MapValue: ArchiveMaps, ClassValue: ExternalClass) -> None:
    if type(ClassValue) is not ExternalClass:
        raise TypeError("external class binding requires an external descriptor")
    if ClassValue.IndexValue >= MapValue.BaseValue:
        raise ValueError("external class binding is outside the inherited prefix")
    EntryValue = MapValue.EntryMap.get(ClassValue.IndexValue)
    if EntryValue is not None:
        if EntryValue.EntryValue != ClassValue:
            raise ValueError("external class binding conflicts with its existing slot")
        return
    PutEntryMut(MapValue, MapEntry(ClassValue.IndexValue, ClassValue))
