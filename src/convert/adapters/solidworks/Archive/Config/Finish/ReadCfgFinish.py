from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FinishFields import (
    KFinishFields,
    KFinishType,
)
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# one bounded finish body belongs to the actual linked ordinary part archive
def ReadCfgFinish(
    BufferValue: bytes,
    VersionValue: int,
    PartValue: ArchiveNode,
    MapValue: ArchiveMaps,
) -> dict[str, object]:
    if type(VersionValue) is not int or VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS finish helper requires archive version 19000")
    PartIndex = ObjectIndex(MapValue, PartValue)
    if (
        PartValue.ClassValue != KPartRoot
        or PartIndex is None
        or PartIndex != PartValue.IndexValue
        or PartIndex >= MapValue.BaseValue
        or KPartRoot not in MapValue.ClassLookup
    ):
        raise BodyUnsupported(
            "SOLIDWORKS finish helper requires its inherited part owner"
        )
    ContextValue = BodyContext(VersionValue, KFinishFields, {}, {})
    Cursor = BinaryReader(BufferValue)
    ReaderValue = GraphReader(Cursor, MapValue, PartialValue(ReadBodyMut, ContextValue))
    FieldsValue: dict[str, object] = {}
    ReadSchemaMut(
        ReadFrame(
            ContextValue,
            ReaderValue,
            FieldScope(FieldsValue),
            PartValue,
            ReadSchemaMut,
            ReadFieldsMut,
        ),
        KFinishType,
    )
    if Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS finish helper has trailing data")
    return FieldsValue
