from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# separate mate streams must retain the inherited identities without changing resolved group children
@DataClass(frozen=True, slots=True)
class MatesGraph:
    RootsValue: tuple[ArchiveNode, ...]
    MapValue: MapSnapshot
    MapBase: int
    VersionValue: int
    ContextValue: Mapping[str, int]
    ReportValue: Mapping[str, object]
