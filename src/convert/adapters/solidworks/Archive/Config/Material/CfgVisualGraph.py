from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.Link.CfgPartStart import CfgPartStart
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the bounded prefix hands back its real visual node and the cursor and map needed by later owners
@DataClass(frozen=True, slots=True)
class CfgVisualGraph:
    StartValue: CfgPartStart
    VisualValue: ArchiveNode
    MapValue: MapSnapshot
    NextOffset: int
    ReportValue: Mapping[str, object]
