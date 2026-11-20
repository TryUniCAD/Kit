from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ReadObjectMut import ReadObjectMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNodeBodyMut import ReadNodeBodyMut
from convert.adapters.solidworks.Archive.Reading.ReadTypeDescMut import ReadTypeDescMut
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag

# deeply nested input must fail before exhausting the process stack
KMaxNestedNodes = 128


# class and object resolution must advance through the same shared cursor
def ReadNodeMut(ReaderValue: GraphReader) -> ArchiveNode | None:
    Cursor = ReaderValue.Cursor
    NodeReader = ObjectRead(
        ReaderValue.MapValue,
        PartialValue(ReadNodeTagMut, Cursor, ReaderValue.NestingDepth),
        PartialValue(ReadTypeDescMut, Cursor),
        PartialValue(ReadNodeBodyMut, ReaderValue),
        MakeArchiveNode if ReaderValue.NodeFactory is None else ReaderValue.NodeFactory,
        Cursor.GetOffset,
    )
    NodeValue = ReadObjectMut(NodeReader)
    if NodeValue is not None and not isinstance(NodeValue, ArchiveNode):
        raise ValueError("SOLIDWORKS stream has an unresolved external object")
    return NodeValue


# references must resolve at the depth limit without opening another body
def ReadNodeTagMut(Cursor: BinaryReader, NestingDepth: int) -> ArchiveTag:
    TagValue, Offset = ReadTag(Cursor.BytesValue, Cursor.OffsetValue)
    if (
        TagValue.KindValue in ("NewClass", "ClassRef")
        and NestingDepth >= KMaxNestedNodes
    ):
        raise ValueError("SOLIDWORKS archive nesting exceeds the supported depth")
    Cursor.OffsetValue = Offset
    return TagValue


# object identities require a separate field owner as soon as a tag allocates one
def MakeArchiveNode(ClassValue: RuntimeClass | ExternalClass) -> ArchiveNode:
    return ArchiveNode(ClassValue, {})
