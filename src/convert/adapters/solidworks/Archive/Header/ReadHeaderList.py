from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KLogFields,
    KStampFields,
)
from convert.adapters.solidworks.Archive.Header.ReadHeaderWire import ReadWireFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# header object collections must preserve shared pointer identity and ordering
def ReadListMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Count = ReadCountMut(ReaderValue.Cursor, 2)
    NodeValue.FieldsValue["items"] = tuple(
        ReadNodeMut(ReaderValue) for _ in range(Count)
    )


# header string arrays must consume strings even when their records are metadata
def ReadTextListMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Count = ReadCountMut(ReaderValue.Cursor, 1)
    Strings = tuple(ReadCStringMut(ReaderValue.Cursor) for _ in range(Count))
    NodeValue.FieldsValue["values"] = Strings
    NodeValue.FieldsValue["items"] = tuple(Value.TextValue for Value in Strings)


# log records share the object list prefix and have their own owner suffix
def ReadLogMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    ReadListMut(ReaderValue, NodeValue)
    Fields = ReadWireFields(ReaderValue, KLogFields)
    NodeValue.FieldsValue.update(Fields)
    NodeValue.FieldsValue["id"] = CastValue(int, Fields["f48"]) & 0xFFFFFFFF
    NodeValue.FieldsValue["name"] = CastValue(CStringValue, Fields["f50"]).TextValue


# stamp records keep version and time separate from the recorded operation name
def ReadStampMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Fields = ReadWireFields(ReaderValue, KStampFields)
    NodeValue.FieldsValue.update(Fields)
    NodeValue.FieldsValue["operation"] = CastValue(
        CStringValue, Fields["f20"]
    ).TextValue
