from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# metadata proof must retain the actual typed root complete map and used grammar without borrowing source archive bytes
@DataClass(frozen=True, slots=True)
class HistoryGraph:
    RootValue: ArchiveNode
    MapValue: MapSnapshot
    VersionValue: int
    ReportValue: Mapping[str, object]
