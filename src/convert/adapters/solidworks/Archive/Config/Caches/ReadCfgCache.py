from functools import partial as PartialValue
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
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
from convert.adapters.solidworks.Archive.Config.Caches.CacheLayouts import KCacheLayouts
from convert.adapters.solidworks.Archive.Config.Caches.CacheRules import KPartCacheRules
from convert.adapters.solidworks.Archive.Config.Caches.CfgCacheGraph import (
    CfgCacheGraph,
)
from convert.adapters.solidworks.Archive.Config.Caches.CheckCachePart import (
    CheckCachePart,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# a selected inline cache must consume its entire field before exposing a completed graph
def ReadCfgCache(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    PartValue: ArchiveNode,
    CacheKind: str,
) -> CfgCacheGraph:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS configuration cache requires archive version 19000"
        )
    RulesValue = KPartCacheRules.get(CacheKind)
    if RulesValue is None:
        raise BodyUnsupported("unsupported SOLIDWORKS configuration cache field")
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    CheckCachePart(PartValue, MapValue)
    ContextValue = BodyContext(VersionValue, KCacheLayouts, {}, {})
    ContextValue.UsageValue.SchemaPath.extend(("moPart_c", "moPart_c.FUN_4c2378b0"))
    ReaderValue = GraphReader(
        BinaryReader(BufferValue), MapValue, PartialValue(ReadBodyMut, ContextValue)
    )
    FieldsValue: dict[str, object] = {}
    FrameValue = ReadFrame(
        ContextValue,
        ReaderValue,
        FieldScope(FieldsValue),
        PartValue,
        ReadSchemaMut,
        ReadFieldsMut,
    )
    ReadFieldsMut(FrameValue, RulesValue)
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS configuration cache has trailing data")
    ContextValue.UsageValue.IsComplete = True
    return CfgCacheGraph(
        MappingProxyType(FieldsValue),
        MapValue.Snapshot(),
        GetBodyReport(ContextValue.UsageValue),
    )
