from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTagMut import (
    WriteTagMut,
    WriteTypeMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import KMaxNestedNodes


# object emission must preserve shared identities and cycles under a bounded native graph depth
def WriteNodeMut(WriterValue: BodyWriter, Value: object) -> None:
    if WriterValue.NestingDepth >= KMaxNestedNodes:
        raise ValueError("SOLIDWORKS body nesting exceeds the supported depth")
    NodeValue = None if Value is None else ArchiveNode.RequireNode(Value)
    ObjectWriter = ObjectStore(
        WriterValue.MapValue,
        PartialValue(WriteTagMut, WriterValue),
        PartialValue(WriteTypeMut, WriterValue),
        PartialValue(WriterValue.NodeBody, WriterValue),
    )
    WriterValue.NestingDepth += 1
    try:
        WriteObjectMut(ObjectWriter, NodeValue)
    finally:
        WriterValue.NestingDepth -= 1
