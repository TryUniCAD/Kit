from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# lightweight header proof needs its actual root map and used grammar independently of the full configuration manager stream
@DataClass(frozen=True, slots=True)
class ManagerGraph:
    RootValue: ArchiveNode
    MapValue: MapSnapshot
    VersionValue: int
    ReportValue: Mapping[str, object]
