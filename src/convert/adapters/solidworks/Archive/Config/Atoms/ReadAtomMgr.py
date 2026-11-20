from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Atoms.AtomMgrGraph import AtomMgrGraph
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import (
    KAtomMgrSchema,
    KPartClass,
)
from convert.adapters.solidworks.Archive.Config.Atoms.CheckAtomMgr import CheckAtomMgr
from convert.adapters.solidworks.Archive.Config.Atoms.MakeAtomCtx import MakeAtomCtx
from convert.adapters.solidworks.Archive.Config.Atoms.ReadAtomNodeMut import (
    ReadAtomNodeMut,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the inline manager keeps the part and its existing map while adding actual atom owners
def ReadAtomMgr(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    ModelValue: ArchiveNode,
    *,
    ConditionBits: int = 0,
) -> AtomMgrGraph:
    ContextValue = MakeAtomCtx(VersionValue, ConditionBits)
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    if ModelValue.ClassValue != KPartClass or ObjectIndex(MapValue, ModelValue) is None:
        raise BodyUnsupported("SOLIDWORKS atom manager requires its mapped part owner")
    ReaderValue = GraphReader(
        BinaryReader(BufferValue), MapValue, PartialValue(ReadAtomNodeMut, ContextValue)
    )
    Fields: dict[str, object] = {}
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(Fields),
        ModelValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadSchemaMut(FrameValue, KAtomMgrSchema)
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS atom manager has trailing data")
    CheckAtomMgr(Fields, MapValue)
    ContextValue.UsageValue.IsComplete = True
    return AtomMgrGraph(
        Fields, MapValue.Snapshot(), GetBodyReport(ContextValue.UsageValue)
    )
