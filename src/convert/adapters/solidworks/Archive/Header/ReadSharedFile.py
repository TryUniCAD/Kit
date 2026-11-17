from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadTextMut
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


# shared file records own path spelling and kind before occurrence state begins
def ReadFileRefMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Cursor = ReaderValue.Cursor
    PathValue = ReadHandleMut(ReaderValue)
    NameValue = ReadHandleMut(ReaderValue)
    KindValue = Cursor.ReadUnsigned(2)
    _ = Cursor.TakeBytes(5)
    for _ in range(3):
        _ = ReadTextMut(Cursor)
    _ = Cursor.TakeBytes(1)
    _ = Cursor.TakeBytes(17)
    ConfigValue = ReadTextMut(Cursor)
    _ = Cursor.TakeBytes(16)
    NodeValue.FieldsValue["file"] = NativeFileRef(
        PathValue, NameValue, KindValue, ConfigValue
    )


# a handle can refer to an already decoded string in the shared archive map
def ReadHandleMut(ReaderValue: GraphReader) -> str:
    Handle = ReadTypedMut(ReaderValue, "moCStringHandle_c", AllowNull=True)
    if Handle is None:
        return ""
    TextValue = Handle.FieldsValue.get("text")
    if not isinstance(TextValue, str):
        raise ValueError("SOLIDWORKS file reference has an incomplete text handle")
    return TextValue


# directory paths must share the serialized text handle grammar with their names
def ReadNameMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    NodeValue.FieldsValue["text"] = ReadTextMut(ReaderValue.Cursor)
