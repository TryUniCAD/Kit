from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the typed unit table must preserve its graph and occupied slots for the next owner
@DataClass(frozen=True, slots=True)
class UnitTableGraph:
    RootValue: ArchiveNode
    MapValue: MapSnapshot
    ReportValue: Mapping[str, object]
