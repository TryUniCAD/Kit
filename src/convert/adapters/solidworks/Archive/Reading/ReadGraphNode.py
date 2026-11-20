from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.ObjectRead import ObjectRead
from convert.adapters.solidworks.Archive.Objects.ReadObjectMut import ReadObjectMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNodeBodyMut import ReadNodeBodyMut
from convert.adapters.solidworks.Archive.Reading.ReadNodeTagMut import ReadNodeTagMut
from convert.adapters.solidworks.Archive.Reading.ReadTypeDescMut import ReadTypeDescMut

# deeply nested input must fail before exhausting the process stack
KMaxNestedNodes = 128


# class and object resolution must advance through the same shared cursor
def ReadNodeMut(ReaderValue: GraphReader) -> ArchiveNode | None:
    Cursor = ReaderValue.Cursor
    NodeReader = ObjectRead(
        ReaderValue.MapValue,
        PartialValue(
            ReadNodeTagMut,
            Cursor,
            ReaderValue.NestingDepth,
            KMaxNestedNodes,
            RequireCanonicalTags=ReaderValue.RequireCanonicalTags,
        ),
        PartialValue(ReadTypeDescMut, Cursor),
        PartialValue(ReadNodeBodyMut, ReaderValue),
        MakeArchiveNode if ReaderValue.NodeFactory is None else ReaderValue.NodeFactory,
        Cursor.GetOffset,
    )
    NodeValue = ReadObjectMut(NodeReader)
    if NodeValue is not None and not isinstance(NodeValue, ArchiveNode):
        raise ValueError("SOLIDWORKS stream has an unresolved external object")
    return NodeValue


# object identities require a separate field owner as soon as a tag allocates one
def MakeArchiveNode(ClassValue: RuntimeClass | ExternalClass) -> ArchiveNode:
    return ArchiveNode(ClassValue, {})
