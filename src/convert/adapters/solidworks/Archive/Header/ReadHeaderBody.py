from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderFields
from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Archive.Header.ReadFileTable import (
    GetFileRef,
    GetFileTable,
)
from convert.adapters.solidworks.Archive.Header.ReadHeaderWire import ReadWireFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the current header separates authored file identity from derived bounds
def ReadHeadMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Fields = ReadWireFields(ReaderValue, KHeaderFields)
    Directory = CastValue(ArchiveNode | None, Fields["f30"])
    Document = CastValue(ArchiveNode | None, Fields["f38"])
    Bounds = CastValue(tuple[float, ...] | None, Fields["bbox"])
    NodeValue.FieldsValue.update(Fields)
    NodeValue.FieldsValue["directory"] = Directory
    if Document is not None:
        NodeValue.FieldsValue["header"] = NativeHeader(
            GetFileRef(Document), GetFileTable(Directory), Bounds
        )
