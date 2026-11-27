from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# configuration graphs retain exact header aliases and map ownership before linked resolved loading
@DataClass(frozen=True, slots=True)
class ConfigGraph:
    RootValue: ArchiveNode
    HeaderValue: ArchiveNode
    MapValue: MapSnapshot
    MapBase: int
    ReportValue: Mapping[str, object]
    VersionValue: int
    ContextValue: Mapping[str, int]
