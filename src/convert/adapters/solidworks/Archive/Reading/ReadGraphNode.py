from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ReadObjectMut import ReadObjectMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag

# deeply nested input must fail before exhausting the process stack
KMaxNestedNodes = 128


# class and object resolution must advance through the same shared cursor
def ReadNodeMut(ReaderValue: GraphReader) -> ArchiveNode | None:
    Cursor = ReaderValue.Cursor
    if ReaderValue.NestingDepth >= KMaxNestedNodes:
        raise ValueError("SOLIDWORKS archive nesting exceeds the supported depth")
    NodeReader = ObjectRead(
        ReaderValue.MapValue,
        PartialValue(ReadTagMut, Cursor),
        PartialValue(ReadTypeDescMut, Cursor),
        PartialValue(ReaderValue.BodyReader, ReaderValue),
        MakeArchiveNode,
        Cursor.GetOffset,
    )
    ReaderValue.NestingDepth += 1
    try:
        NodeValue = ReadObjectMut(NodeReader)
    finally:
        ReaderValue.NestingDepth -= 1
    if NodeValue is not None and not isinstance(NodeValue, ArchiveNode):
        raise ValueError("SOLIDWORKS stream has an unresolved external object")
    return NodeValue


# the existing tag reader owns the wire form while the cursor owns position
def ReadTagMut(Cursor: BinaryReader) -> ArchiveTag:
    TagValue, Offset = ReadTag(Cursor.BytesValue, Cursor.OffsetValue)
    Cursor.OffsetValue = Offset
    return TagValue


# native class descriptors precede object bodies and carry an independent schema
def ReadTypeDescMut(Cursor: BinaryReader) -> RuntimeClass:
    Schema = Cursor.ReadUnsigned(2)
    Length = Cursor.ReadUnsigned(2)
    ClassName = Cursor.TakeBytes(Length).decode("ascii")
    return RuntimeClass(ClassName, Schema)


# object identities require a separate field owner as soon as a tag allocates one
def MakeArchiveNode(ClassValue: RuntimeClass | ExternalClass) -> ArchiveNode:
    return ArchiveNode(ClassValue, {})
