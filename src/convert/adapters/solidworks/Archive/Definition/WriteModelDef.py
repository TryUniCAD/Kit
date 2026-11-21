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
from convert.adapters.solidworks.Archive.Definition.ModelDefClsid import (
    KAsmDefClass,
    KModelDefClsids,
    KPartDefClass,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefContext import (
    ModelDefContext,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each native definition derives the root identity and every wire byte from modeled fields
def WriteModelDef(
    GraphValue: ModelDefGraph, *, OrdinaryOnly: bool = False, Assembly: bool = False
) -> DefinitionWire:
    DocumentValue = GraphValue.DocumentValue
    ClassValue = DocumentValue.ClassValue
    ExpectedClass = KAsmDefClass if Assembly else KPartDefClass
    if (Assembly or OrdinaryOnly) and ClassValue != ExpectedClass:
        KindValue = "assembly" if Assembly else "part"
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition requires {ExpectedClass.NameValue} schema 1"
        )
    if not isinstance(ClassValue, RuntimeClass):
        raise BodyUnsupported("SOLIDWORKS model Definition requires a concrete class")
    ClsidValue = KModelDefClsids.get(ClassValue)
    if ClsidValue is None:
        raise BodyUnsupported("unsupported SOLIDWORKS model Definition class")
    ContextValue = ModelDefContext(
        GraphValue.VersionValue, OrdinaryOnly=OrdinaryOnly, Assembly=Assembly
    )
    if Assembly or OrdinaryOnly:
        CheckDefScope(DocumentValue.FieldsValue, Assembly=Assembly)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(DocumentValue.FieldsValue),
        DocumentValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteFieldsMut(FrameValue, KDefPrefixFields)
    WriterValue.OutputValue.extend(ClsidValue)
    WriteBodyMut(WriterValue, DocumentValue)
    ContextValue.UsageValue.IsComplete = True
    return DefinitionWire(
        bytes(WriterValue.OutputValue),
        WriterValue.MapValue.Snapshot(),
        ContextValue.UsageValue,
    )
