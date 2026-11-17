from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Archive.Header.ReadFileTable import (
    GetFileRef,
    GetFileTable,
)
from convert.adapters.solidworks.Archive.Header.ReadHeaderBounds import ReadBoundsMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


# the current header separates authored file identity from derived bounds
def ReadHeadMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Cursor = ReaderValue.Cursor
    _ = Cursor.TakeBytes(4)
    _ = ReadTypedMut(ReaderValue, "su_CStringArray", AllowNull=True)
    _ = ReadTypedMut(ReaderValue, "su_CStringArray", AllowNull=True)
    _ = ReadTypedMut(ReaderValue, "suObList", AllowNull=True)
    _ = Cursor.TakeBytes(8)
    Directory = ReadTypedMut(ReaderValue, "moExtObjectList_c", AllowNull=True)
    _ = Cursor.TakeBytes(4)
    Document = ReadTypedMut(ReaderValue, "moExtObject_c")
    _ = Cursor.TakeBytes(28)
    if ReadNodeMut(ReaderValue) is not None:
        raise ValueError("unsupported SOLIDWORKS header configuration object")
    _ = Cursor.TakeBytes(12)
    _ = ReadTypedMut(ReaderValue, "suObList", AllowNull=True)
    _ = Cursor.TakeBytes(8)
    Bounds = ReadBoundsMut(Cursor)
    _ = Cursor.TakeBytes(80)
    NodeValue.FieldsValue["header"] = NativeHeader(
        GetFileRef(Document), GetFileTable(Directory), Bounds
    )
    NodeValue.FieldsValue["directory"] = Directory
