from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
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
from convert.adapters.solidworks.Drawing.Definition.Emission.DefinitionRead import (
    DefinitionRead,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import (
    KBlankLayouts,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadDrawMut import (
    ReadDrawMut,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# complete generated definitions need a reader that consumes the ui tail and all model owners
def ReadBlankDef(DataValue: bytes, VersionValue: int) -> DefinitionRead:
    if VersionValue != 19000:
        raise BodyUnsupported("blank drawing Definition requires archive version 19000")
    ContextValue = BodyContext(
        VersionValue, KBlankLayouts, KBlankVirtuals, KBlankSchemas
    )
    CursorValue = BinaryReader(DataValue)
    ReaderValue = GraphReader(
        CursorValue, ArchiveMaps(1), PartialValue(ReadDrawMut, ContextValue)
    )
    DocumentValue = ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), {})
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(DocumentValue.FieldsValue),
        DocumentValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadFieldsMut(FrameValue, KDefPrefixFields)
    ClsidValue = CursorValue.TakeBytes(len(KDrawClsid))
    if ClsidValue != KDrawClsid:
        raise BodyUnsupported("blank drawing Definition has the wrong document clsid")
    DocumentValue.FieldsValue.update(
        clsid_a=int.from_bytes(ClsidValue[:4], "little"),
        clsid_b=int.from_bytes(ClsidValue[4:6], "little"),
        clsid_c=int.from_bytes(ClsidValue[6:8], "little"),
        clsid_d=ClsidValue[8:],
    )
    ReadBodyMut(ContextValue, ReaderValue, DocumentValue)
    if CursorValue.GetRemaining() != 0:
        raise BodyUnsupported("blank drawing Definition has unconsumed tail bytes")
    GraphValue = BlankGraph(DocumentValue, VersionValue)
    CheckBlankGraph(GraphValue)
    for NodeValue in WalkDrawNodes(DocumentValue):
        CheckBlankNode(NodeValue)
    ContextValue.UsageValue.IsComplete = True
    return DefinitionRead(
        GraphValue, ReaderValue.MapValue.Snapshot(), ContextValue.UsageValue
    )
