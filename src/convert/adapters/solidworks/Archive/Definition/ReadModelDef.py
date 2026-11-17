from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefClsid import ReadDefClass
from convert.adapters.solidworks.Archive.Definition.ModelDefContext import (
    ModelDefContext,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.ModelDefRead import ModelDefRead
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# the root must consume the complete stream before its typed settings may be used
def ReadModelDef(DataValue: bytes, VersionValue: int) -> ModelDefRead:
    ContextValue = ModelDefContext(VersionValue)
    CursorValue = BinaryReader(DataValue)
    ReaderValue = GraphReader(
        CursorValue, ArchiveMaps(1), PartialValue(ReadBodyMut, ContextValue)
    )
    Prefix: dict[str, object] = {
        RuleValue.NameValue: ReadScalarMut(CursorValue, RuleValue.TypeValue)
        for RuleValue in KDefPrefixFields
    }
    ClassValue = ReadDefClass(CursorValue.TakeBytes(16))
    DocumentValue = ArchiveNode(ClassValue, Prefix)
    ReadBodyMut(ContextValue, ReaderValue, DocumentValue)
    if CursorValue.GetRemaining() != 0:
        raise BodyUnsupported("SOLIDWORKS model Definition has an unconsumed tail")
    ContextValue.UsageValue.IsComplete = True
    return ModelDefRead(
        ModelDefGraph(DocumentValue, VersionValue),
        ReaderValue.MapValue.Snapshot(),
        ContextValue.UsageValue,
    )
