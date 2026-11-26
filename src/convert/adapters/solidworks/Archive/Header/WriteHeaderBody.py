from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KHeaderFields,
    KLogFields,
    KStampFields,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderFile import StoreFileMut
from convert.adapters.solidworks.Archive.Header.WriteHeaderList import (
    StoreObjListMut,
    StoreTextsMut,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderWire import (
    StoreFieldsMut,
    StoreTextMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


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
            StoreTextsMut(Buffer, Fields["values"])
        case _:
            raise ValueError("unsupported SOLIDWORKS header object body")
