from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import (
    KAtomMgrSchema,
    KPartClass,
)
from convert.adapters.solidworks.Archive.Config.Atoms.CheckAtomMgr import CheckAtomMgr
from convert.adapters.solidworks.Archive.Config.Atoms.MakeAtomCtx import MakeAtomCtx
from convert.adapters.solidworks.Archive.Config.Atoms.PutAtomBodyMut import (
    PutAtomBodyMut,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# emission derives a complete bounded manager in a private map before returning any bytes
def WriteAtomMgr(
    FieldsValue: Mapping[str, object],
    VersionValue: int,
    SeedValue: MapSnapshot,
    ModelValue: ArchiveNode,
    *,
    ConditionBits: int = 0,
) -> tuple[bytes, MapSnapshot]:
    ContextValue = MakeAtomCtx(VersionValue, ConditionBits)
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    if ModelValue.ClassValue != KPartClass or ObjectIndex(MapValue, ModelValue) is None:
        raise BodyUnsupported("SOLIDWORKS atom manager requires its mapped part owner")
    WriterValue = BodyWriter(MapValue, ContextValue, PutAtomBodyMut)
    Fields = dict(FieldsValue)
    ScopeValue = FieldScope(Fields)
    FrameValue = WriteFrame(
        WriterValue, ScopeValue, ModelValue, WriteSchemaMut, WriteFieldsMut
    )
    WriteSchemaMut(FrameValue, KAtomMgrSchema)
    CheckAtomMgr({**Fields, **ScopeValue.ValuesValue}, MapValue)
    return bytes(WriterValue.OutputValue), MapValue.Snapshot()
