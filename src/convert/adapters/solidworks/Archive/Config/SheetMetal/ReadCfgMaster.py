from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import (
    ReadFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import (
    ReadSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.SheetMetal.CheckMaster import (
    CheckMaster,
)
from convert.adapters.solidworks.Archive.Config.SheetMetal.MasterRules import (
    KMasterBridge,
    KMasterClass,
    KMasterLayouts,
    KMasterVirtuals,
)
from convert.adapters.solidworks.Archive.Config.SheetMetal.NoMasterRef import (
    NoMasterRef,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the complete bounded bridge must preserve its inherited map and leave the part untouched
def ReadCfgMaster(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    PartValue: ArchiveNode,
) -> ArchiveNode | None:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master requires archive version 19000"
        )
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    if PartValue.ClassValue != KPartRoot or ObjectIndex(MapValue, PartValue) is None:
        raise BodyUnsupported(
            "SOLIDWORKS sheet metal master requires its mapped part owner"
        )
    ContextValue = BodyContext(VersionValue, KMasterLayouts, KMasterVirtuals, {})
    ReaderValue = GraphReader(BinaryReader(BufferValue), MapValue, NoMasterRef)
    Fields: dict[str, object] = {}
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(Fields),
        PartValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadFieldsMut(FrameValue, KMasterBridge)
    if ReaderValue.Cursor.GetRemaining() or MapValue.Snapshot() != SeedValue:
        raise BodyUnsupported("unqualified SOLIDWORKS sheet metal master boundary")
    if "f1018" not in Fields:
        return None
    NodeValue = ArchiveNode.RequireNode(Fields["f1018"])
    if NodeValue.ClassValue != KMasterClass or NodeValue.IndexValue is not None:
        raise BodyUnsupported("SOLIDWORKS sheet metal master requires its direct owner")
    CheckMaster(NodeValue)
    return NodeValue
