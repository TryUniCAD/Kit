from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankSchemas import (
    KBlankSchemas,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankVirtuals import (
    KBlankVirtuals,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankGraph import (
    CheckBlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankNode import (
    CheckBlankNode,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.DefinitionWire import (
    DefinitionWire,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import (
    KBlankLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.ScalarFields import (
    MakeScalarRows,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawMut import (
    WriteDrawMut,
)
from convert.adapters.solidworks.Drawing.Definition.Writing.CheckSheetData import (
    CheckSheetData,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# a complete stream must compute every native tag and tail from its admitted graph before returning bytes
def WriteBlankDef(GraphValue: BlankGraph) -> DefinitionWire:
    CheckBlankGraph(GraphValue)
    ContextValue = BodyContext(
        GraphValue.VersionValue, KBlankLayouts, KBlankVirtuals, KBlankSchemas
    )
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteDrawMut)
    for NodeValue in WalkDrawNodes(GraphValue.DocumentValue):
        ClassValue = NodeValue.ClassValue
        if not (
            isinstance(ClassValue, RuntimeClass)
            and (ClassValue.NameValue, ClassValue.SchemaValue) in KHeaderClasses
        ):
            _ = CheckBodyMut(ContextValue, NodeValue)
        CheckBlankNode(NodeValue)
        if ClassValue == RuntimeClass("moDrSheet", 1):
            CheckSheetData(WriterValue, NodeValue)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(GraphValue.DocumentValue.FieldsValue),
        GraphValue.DocumentValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteFieldsMut(FrameValue, MakeScalarRows("i32", "fa58 fa5c fa60 fa64 fa74"))
    WriterValue.OutputValue.extend(KDrawClsid)
    WriteBodyMut(WriterValue, GraphValue.DocumentValue)
    ContextValue.UsageValue.IsComplete = True
    return DefinitionWire(
        bytes(WriterValue.OutputValue),
        WriterValue.MapValue.Snapshot(),
        ContextValue.UsageValue,
    )
