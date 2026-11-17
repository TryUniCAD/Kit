from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


# header readback has its own complete map and must consume the complete stream
def ReadHeader(DataValue: bytes, Version: int) -> NativeHeader:
    RootValue = ReadHeaderGraph(DataValue, Version)
    Header = RootValue.FieldsValue.get("header")
    if not isinstance(Header, NativeHeader):
        raise ValueError("SOLIDWORKS header has no self file identity")
    return Header


# the complete header graph supplies the same identities to linked native streams
def ReadHeaderGraph(DataValue: bytes, Version: int) -> ArchiveNode:
    if Version != KHeaderVersion:
        raise ValueError(f"unsupported SOLIDWORKS header archive version {Version}")
    Cursor = BinaryReader(DataValue)
    ReaderValue = GraphReader(Cursor, ArchiveMaps(1), ReadHeaderClass)
    NodeValue = ReadTypedMut(ReaderValue, "moHeader_c")
    if NodeValue is None or Cursor.GetRemaining():
        raise ValueError("SOLIDWORKS header has an incomplete root or trailing data")
    return NodeValue


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
