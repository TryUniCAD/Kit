from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Writing.CheckSheetData import (
    CheckSheetData,
)
from convert.adapters.solidworks.Drawing.Definition.Writing.SheetFields import (
    KSheetFields,
)


# drawing sheet fields must continue the existing native map through the shared typed executor
def WriteSheetMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    CheckSheetData(WriterValue, NodeValue)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(NodeValue.FieldsValue),
        NodeValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteFieldsMut(FrameValue, KSheetFields)
