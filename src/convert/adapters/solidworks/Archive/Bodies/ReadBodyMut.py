from collections.abc import Callable

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# class admission and field decoding must use the existing shared graph identity
def ReadBodyMut(
    ContextValue: BodyContext,
    ReaderValue: GraphReader,
    NodeValue: ArchiveNode,
    *,
    SchemaReader: Callable[[ReadFrame, str], None] = ReadSchemaMut,
) -> None:
    ClassName = CheckBodyMut(ContextValue, NodeValue)
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(NodeValue.FieldsValue),
        NodeValue,
        SchemaReader,
        ReadFieldsMut,
    )
    SchemaReader(FrameValue, ClassName)
