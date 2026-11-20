from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTagMut import (
    WriteTagMut,
    WriteTypeMut,
)
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import KMaxNestedNodes


# object emission must preserve shared identities and cycles under a bounded native graph depth
def WriteNodeMut(WriterValue: BodyWriter, Value: object) -> None:
    NodeValue = None if Value is None else ArchiveNode.RequireNode(Value)
    if (
        NodeValue is not None
        and WriterValue.NestingDepth >= KMaxNestedNodes
        and ObjectIndex(WriterValue.MapValue, NodeValue) is None
    ):
        raise ValueError("SOLIDWORKS body nesting exceeds the supported depth")
    ObjectWriter = ObjectStore(
        WriterValue.MapValue,
        PartialValue(WriteTagMut, WriterValue),
        PartialValue(WriteTypeMut, WriterValue),
        PartialValue(StoreBodyMut, WriterValue),
    )
    WriteObjectMut(ObjectWriter, NodeValue)


# only live body callbacks consume a depth slot while terminal tags still resolve
def StoreBodyMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    WriterValue.NestingDepth += 1
    try:
        WriterValue.NodeBody(WriterValue, NodeValue)
    finally:
        WriterValue.NestingDepth -= 1
