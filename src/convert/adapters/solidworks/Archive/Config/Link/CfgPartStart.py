from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# header alias identity stays available before any model fields are decoded
@DataClass(frozen=True, slots=True)
class CfgPartStart:
    HeaderValue: ArchiveNode
    RootValue: ArchiveNode
    MapValue: MapSnapshot
    BaseValue: int
    LightOffset: int
    LightSize: int
