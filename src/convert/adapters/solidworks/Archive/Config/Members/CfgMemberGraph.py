from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# member reads preserve optional object identity and the exact archive handoff
@DataClass(frozen=True, slots=True)
class CfgMemberGraph:
    RootValue: ArchiveNode | None
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
