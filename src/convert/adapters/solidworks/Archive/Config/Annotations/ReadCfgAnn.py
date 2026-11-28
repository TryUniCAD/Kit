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
from convert.adapters.solidworks.Archive.Config.Annotations.AnnLayouts import (
    KAnnDefs,
    KAnnLayouts,
    KTolHelper,
)
from convert.adapters.solidworks.Archive.Config.Annotations.CheckTolFrames import (
    CheckTolFrames,
)
from convert.adapters.solidworks.Archive.Config.Link.CfgPartStart import CfgPartStart
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# detailing intervals need an actual part owner and a bounded map inert body
def ReadCfgAnn(
    BufferValue: bytes,
    VersionValue: int,
    PartValue: CfgPartStart,
    LayoutName: str,
    *,
    Conditions: int = 0,
) -> dict[str, object]:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS configuration annotation requires archive version 19000"
        )
    if LayoutName not in (KAnnDefs, KTolHelper):
        raise BodyUnsupported(
            "SOLIDWORKS configuration annotation has an unsupported inline owner"
        )
    MapsValue = ArchiveMaps(PartValue.BaseValue, PartValue.MapValue)
    RootValue = PartValue.RootValue
    if RootValue.ClassValue != KPartRoot or ObjectIndex(MapsValue, RootValue) != 2:
        raise BodyUnsupported(
            "SOLIDWORKS configuration annotation requires its enclosing part"
        )
    ContextValue = BodyContext(
        VersionValue,
        KAnnLayouts,
        {},
        {},
        FlagsValue={"conditions": Conditions, "bounded_config_annotations": 1},
    )
    Cursor = BinaryReader(BufferValue)
    ReaderValue = GraphReader(
        Cursor,
        MapsValue,
        PartialValue(ReadBodyMut, ContextValue),
        RequireCanonicalTags=True,
    )
    FieldsValue: dict[str, object] = {}
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(FieldsValue),
        RootValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadSchemaMut(FrameValue, LayoutName)
    if Cursor.GetRemaining() or MapsValue.Snapshot() != PartValue.MapValue:
        raise BodyUnsupported(
            "SOLIDWORKS configuration annotation changed its bounded body or map"
        )
    if LayoutName == KTolHelper:
        CheckTolFrames(FieldsValue)
    return FieldsValue
