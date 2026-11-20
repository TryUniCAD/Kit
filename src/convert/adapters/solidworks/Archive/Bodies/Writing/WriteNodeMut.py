from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTagMut import WriteTagMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTypeMut import WriteTypeMut
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import KMaxNestedNodes


# object emission must preserve shared identities and cycles under a bounded native graph depth
def WriteNodeMut(WriterValue: BodyWriter, Value: object) -> None:
    NodeValue = None if Value is None else ArchiveNode.RequireNode(Value)
    DepthValue = WriterValue.NestingDepth
    OpensBody = (
        NodeValue is not None and ObjectIndex(WriterValue.MapValue, NodeValue) is None
    )
    if OpensBody and DepthValue >= KMaxNestedNodes:
        raise ValueError("SOLIDWORKS body nesting exceeds the supported depth")
    ObjectWriter = ObjectStore(
        WriterValue.MapValue,
        PartialValue(WriteTagMut, WriterValue),
        PartialValue(WriteTypeMut, WriterValue),
        PartialValue(WriterValue.NodeBody, WriterValue),
    )
    WriterValue.NestingDepth = DepthValue + int(OpensBody)
    try:
        WriteObjectMut(ObjectWriter, NodeValue)
    finally:
        WriterValue.NestingDepth = DepthValue
