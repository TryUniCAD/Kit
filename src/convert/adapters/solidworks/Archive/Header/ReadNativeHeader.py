from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


# header readback has its own complete map and must consume the complete stream
def ReadHeader(DataValue: bytes, Version: int) -> NativeHeader:
    if Version != 19000:
        raise ValueError(f"unsupported SOLIDWORKS header archive version {Version}")
    Cursor = BinaryReader(DataValue)
    ReaderValue = GraphReader(Cursor, ArchiveMaps(1), ReadHeaderClass)
    NodeValue = ReadTypedMut(ReaderValue, "moHeader_c")
    Header = NodeValue.FieldsValue.get("header") if NodeValue is not None else None
    if not isinstance(Header, NativeHeader) or Cursor.GetRemaining():
        raise ValueError("SOLIDWORKS header has an incomplete root or trailing data")
    return Header


# reused class names must still match the release specific wire schema
def ReadHeaderClass(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    ClassValue = NodeValue.ClassValue
    if not isinstance(ClassValue, RuntimeClass):
        raise ValueError("SOLIDWORKS header contains an unresolved class")
    Decoder = KHeaderClasses.get((ClassValue.NameValue, ClassValue.SchemaValue))
    if Decoder is None:
        raise ValueError(
            f"unsupported SOLIDWORKS header class {ClassValue.NameValue} schema {ClassValue.SchemaValue}"
        )
    Decoder(ReaderValue, NodeValue)
