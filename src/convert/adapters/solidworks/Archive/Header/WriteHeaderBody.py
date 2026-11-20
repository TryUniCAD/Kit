from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields,
    KExtTailFields,
    KHeaderFields,
    KLogFields,
    KRefCfgFields,
    KSharedFields,
    KStampFields,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderWire import (
    StoreChildMut,
    StoreFieldsMut,
    StoreTextMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# embedded file definitions preserve typed fields between the owning object fields
def HeaderMapping(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise ValueError("SOLIDWORKS header requires a typed embedded field mapping")
    return CastValue(Mapping[str, object], Value)


# list prefixes derive from their actual immutable item collections
def StoreCountMut(Buffer: bytearray, Value: object) -> tuple[object, ...]:
    if not isinstance(Value, tuple):
        raise ValueError("SOLIDWORKS header requires an ordered tuple of items")
    Items = CastValue(tuple[object, ...], Value)
    Buffer.extend(EncodeCount(len(Items)))
    return Items


# an ordinary file definition writes shared identity before its configuration suffix
def StoreFileMut(
    Buffer: bytearray, WriterValue: ObjectStore, Fields: Mapping[str, object]
) -> None:
    StoreFieldsMut(Buffer, WriterValue, KSharedFields, HeaderMapping(Fields["shared"]))
    StoreFieldsMut(Buffer, WriterValue, KExtLeadFields, Fields)
    StoreFieldsMut(Buffer, WriterValue, KRefCfgFields, HeaderMapping(Fields["refcfg"]))
    StoreFieldsMut(Buffer, WriterValue, KExtTailFields, Fields)


# object lists retain the same serialized sequence before any class specific suffix
def StoreObjListMut(
    Buffer: bytearray, WriterValue: ObjectStore, Fields: Mapping[str, object]
) -> None:
    for ItemValue in StoreCountMut(Buffer, Fields["items"]):
        StoreChildMut(WriterValue, ItemValue)


# the native header registry bounds the classes consumed in either direction
def StoreHeaderBody(
    Buffer: bytearray, WriterValue: ObjectStore, NodeValue: ArchiveNode
) -> None:
    ClassValue = NodeValue.ClassValue
    if (
        not isinstance(ClassValue, RuntimeClass)
        or (
            ClassValue.NameValue,
            ClassValue.SchemaValue,
        )
        not in KHeaderClasses
    ):
        raise ValueError("unsupported SOLIDWORKS header object class")
    Fields = NodeValue.FieldsValue
    match ClassValue.NameValue:
        case "moHeader_c":
            StoreFieldsMut(Buffer, WriterValue, KHeaderFields, Fields)
        case "moExtObject_c":
            StoreFileMut(Buffer, WriterValue, Fields)
        case "moExtObjectList_c" | "suObList":
            StoreObjListMut(Buffer, WriterValue, Fields)
        case "moLogs_c":
            StoreObjListMut(Buffer, WriterValue, Fields)
            StoreFieldsMut(Buffer, WriterValue, KLogFields, Fields)
        case "moStamp_c":
            StoreFieldsMut(Buffer, WriterValue, KStampFields, Fields)
        case "moCStringHandle_c":
            StoreTextMut(Buffer, Fields["value"])
        case "su_CStringArray":
            for Value in StoreCountMut(Buffer, Fields["values"]):
                StoreTextMut(Buffer, Value)
        case _:
            raise ValueError("unsupported SOLIDWORKS header object body")
