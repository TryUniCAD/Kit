from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# body emission must derive bytes from typed fields under the same concrete grammar
def WriteBodyMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    ClassName = CheckBodyMut(WriterValue.ContextValue, NodeValue)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(NodeValue.FieldsValue),
        NodeValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteSchemaMut(FrameValue, ClassName)
