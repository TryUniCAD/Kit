from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTagMut import WriteTagMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteTypeMut import WriteTypeMut
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Header.WriteHeaderBody import StoreHeaderBody
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Writing.WriteSheetMut import (
    WriteSheetMut,
)


# inline headers and inherited sheet bodies must retain the surrounding definition object map
def WriteDrawMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    ClassValue = NodeValue.ClassValue
    if (
        isinstance(ClassValue, RuntimeClass)
        and (
            ClassValue.NameValue,
            ClassValue.SchemaValue,
        )
        in KHeaderClasses
    ):
        WriterValue.ContextValue.UsageValue.SchemaCalls[ClassValue.NameValue] += 1
        ObjectWriter = ObjectStore(
            WriterValue.MapValue,
            PartialValue(WriteTagMut, WriterValue),
            PartialValue(WriteTypeMut, WriterValue),
            PartialValue(WriteDrawMut, WriterValue),
        )
        StoreHeaderBody(WriterValue.OutputValue, ObjectWriter, NodeValue)
    elif ClassValue.NameValue == "moDrSheet":
        FrameValue = WriteFrame(
            WriterValue,
            FieldScope(NodeValue.FieldsValue),
            NodeValue,
            WriteSchemaMut,
            WriteFieldsMut,
        )
        WriteSchemaMut(FrameValue, "moModelFeature_c")
        WriteSheetMut(WriterValue, NodeValue)
    else:
        WriteBodyMut(WriterValue, NodeValue)
