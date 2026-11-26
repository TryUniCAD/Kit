from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# external directory members must resolve to real entries before paths can be joined
def GetFileRef(NodeValue: object) -> NativeFileRef:
    if not isinstance(NodeValue, ArchiveNode):
        raise ValueError("SOLIDWORKS header lacks a file entry")
    Entry = NodeValue.FieldsValue.get("file")
    if not isinstance(Entry, NativeFileRef):
        raise ValueError("SOLIDWORKS header file entry has the wrong class")
    return Entry


# no external directory is valid for a document without model links
def GetFileTable(Directory: ArchiveNode | None) -> tuple[NativeFileRef, ...]:
    if Directory is None:
        return ()
    Items = Directory.FieldsValue.get("items")
    if not isinstance(Items, tuple):
        raise ValueError("SOLIDWORKS header file directory is incomplete")
    return tuple(
        GetFileRef(ItemValue) for ItemValue in CastValue(tuple[object, ...], Items)
    )
