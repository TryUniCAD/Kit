from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# independent manager graphs retain original node aliases without borrowing another stream map
@DataClass(frozen=True, slots=True)
class CmgrGraph:
    RootValue: ArchiveNode
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
    VersionValue: int
    ContextValue: Mapping[str, int]
