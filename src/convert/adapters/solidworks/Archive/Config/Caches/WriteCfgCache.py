from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import (
    WriteFieldsMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import (
    WriteSchemaMut,
)
from convert.adapters.solidworks.Archive.Config.Caches.CacheLayouts import KCacheLayouts
from convert.adapters.solidworks.Archive.Config.Caches.CacheRules import KPartCacheRules
from convert.adapters.solidworks.Archive.Config.Caches.CheckCachePart import (
    CheckCachePart,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# bounded cache fragments need an actual mapped part and must never allocate archive entries
def WriteCfgCache(
    FieldsValue: Mapping[str, object],
    VersionValue: int,
    SeedValue: MapSnapshot,
    PartValue: ArchiveNode,
    CacheKind: str,
) -> bytes:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS configuration cache requires archive version 19000"
        )
    RulesValue = KPartCacheRules.get(CacheKind)
    if RulesValue is None:
        raise BodyUnsupported("unsupported SOLIDWORKS configuration cache field")
    RuleValue = RulesValue[0]
    if set(FieldsValue) != {RuleValue.NameValue, RuleValue.OtherName} - {""}:
        raise BodyUnsupported(
            "SOLIDWORKS cache fragment requires exactly its modeled fields"
        )
    MapsValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    CheckCachePart(PartValue, MapsValue)
    ContextValue = BodyContext(VersionValue, KCacheLayouts, {}, {})
    ContextValue.UsageValue.SchemaPath.extend(("moPart_c", "moPart_c.FUN_4c2378b0"))
    WriterValue = BodyWriter(MapsValue, ContextValue, WriteBodyMut)
    FrameValue = WriteFrame(
        WriterValue,
        FieldScope(dict(FieldsValue)),
        PartValue,
        WriteSchemaMut,
        WriteFieldsMut,
    )
    WriteFieldsMut(FrameValue, RulesValue)
    if MapsValue.Snapshot() != SeedValue:
        raise BodyUnsupported("SOLIDWORKS cache fragment changed the part map")
    return bytes(WriterValue.OutputValue)
