from __future__ import annotations

from typing import TYPE_CHECKING as KTypeCheck

from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

if KTypeCheck:
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps


# inverse lookups need strong node owners so python identities cannot be reused
def PutEntryMut(MapValue: ArchiveMaps, EntryValue: MapEntry) -> None:
    if EntryValue.IndexValue in MapValue.EntryMap:
        raise ValueError("archive map slot is already occupied")
    MapValue.EntryMap[EntryValue.IndexValue] = EntryValue
    if isinstance(EntryValue.EntryValue, (RuntimeClass, ExternalClass)):
        MapValue.ClassLookup[EntryValue.EntryValue] = EntryValue.IndexValue
    else:
        MapValue.ObjectLookup[id(EntryValue.EntryValue)] = EntryValue.IndexValue
