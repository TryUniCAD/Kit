from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
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
from convert.adapters.solidworks.Archive.Definition.CheckDefScope import CheckDefScope
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefClsid import KPartDefClass
from convert.adapters.solidworks.Archive.Definition.ModelDefContext import (
    ModelDefContext,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Container.Definition import KPartClsid


# each native definition derives the root identity and every wire byte from modeled fields
def WriteModelDef(GraphValue: ModelDefGraph) -> DefinitionWire:
    DocumentValue = GraphValue.DocumentValue
    if DocumentValue.ClassValue != KPartDefClass:
        raise BodyUnsupported(
            "SOLIDWORKS part Definition requires uiPartDoc_c schema 1"
        )
    ContextValue = ModelDefContext(GraphValue.VersionValue)
    CheckDefScope(DocumentValue.FieldsValue)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(DocumentValue.FieldsValue),
        DocumentValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteFieldsMut(FrameValue, KDefPrefixFields)
    WriterValue.OutputValue.extend(KPartClsid)
    WriteBodyMut(WriterValue, DocumentValue)
    ContextValue.UsageValue.IsComplete = True
    return DefinitionWire(
        bytes(WriterValue.OutputValue),
        WriterValue.MapValue.Snapshot(),
        ContextValue.UsageValue,
    )
