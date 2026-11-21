from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import (
    KDefPrefixFields,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadDrawMut import (
    ReadDrawMut,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.BindFrontMut import (
    BindFrontMut,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import (
    KFrontLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import (
    KFrontSchemas,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import (
    KFrontVirtuals,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# linked definition profiles share the complete wire parse before applying their own semantic admission
def ReadLinkedBody(
    DataValue: bytes, VersionValue: int, ProfileName: str
) -> tuple[ArchiveNode, MapSnapshot, BodyUsage]:
    if VersionValue != 19000:
        raise BodyUnsupported(
            f"{ProfileName} drawing Definition requires archive version 19000"
        )
    ContextValue = BodyContext(
        VersionValue, KFrontLayouts, KFrontVirtuals, KFrontSchemas
    )
    ContextValue.FlagsValue["owner_is_drawing"] = 1
    CursorValue = BinaryReader(DataValue)
    ReaderValue = GraphReader(
        CursorValue, ArchiveMaps(1), PartialValue(ReadDrawMut, ContextValue)
    )
    Document = ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), {})
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(Document.FieldsValue),
        Document,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadFieldsMut(FrameValue, KDefPrefixFields)
    ClsidValue = CursorValue.TakeBytes(len(KDrawClsid))
    if ClsidValue != KDrawClsid:
        raise BodyUnsupported(
            f"{ProfileName} drawing Definition has the wrong document clsid"
        )
    Document.FieldsValue.update(
        clsid_a=int.from_bytes(ClsidValue[:4], "little"),
        clsid_b=int.from_bytes(ClsidValue[4:6], "little"),
        clsid_c=int.from_bytes(ClsidValue[6:8], "little"),
        clsid_d=ClsidValue[8:],
    )
    ReadBodyMut(ContextValue, ReaderValue, Document)
    if CursorValue.GetRemaining() != 0:
        raise BodyUnsupported(
            f"{ProfileName} drawing Definition has unconsumed tail bytes"
        )
    BindFrontMut(Document)
    return Document, ReaderValue.MapValue.Snapshot(), ContextValue.UsageValue
