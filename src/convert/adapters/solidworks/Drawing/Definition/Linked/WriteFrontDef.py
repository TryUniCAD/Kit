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
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankNode import (
    CheckBlankNode,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawMut import (
    WriteDrawMut,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontGraph import (
    CheckFrontGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import (
    KFrontLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import (
    KFrontSchemas,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import (
    KFrontVirtuals,
)
from convert.adapters.solidworks.Drawing.Definition.Writing.CheckSheetData import (
    CheckSheetData,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# one linked view requires a complete surrounding drawing map rather than a separately emitted reference fragment
def WriteFrontDef(GraphValue: FrontGraph) -> DefinitionWire:
    CheckFrontGraph(GraphValue)
    ContextValue = BodyContext(
        GraphValue.VersionValue, KFrontLayouts, KFrontVirtuals, KFrontSchemas
    )
    ContextValue.FlagsValue["owner_is_drawing"] = 1
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
    WriteFieldsMut(FrameValue, KDefPrefixFields)
    WriterValue.OutputValue.extend(KDrawClsid)
    WriteBodyMut(WriterValue, GraphValue.DocumentValue)
    ContextValue.UsageValue.IsComplete = True
    return DefinitionWire(
        bytes(WriterValue.OutputValue),
        WriterValue.MapValue.Snapshot(),
        ContextValue.UsageValue,
    )
