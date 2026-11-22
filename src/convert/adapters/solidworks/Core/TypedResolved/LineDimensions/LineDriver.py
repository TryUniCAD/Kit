from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a point distance must retain its actual parameter display and ordered local point references
@Dataclass(frozen=True, slots=True)
class LineDriver:
    IndexValue: int
    NodeValue: ArchiveNode
    ParamValue: ArchiveNode
    HandleValue: ArchiveNode
    DisplayValue: ArchiveNode
    PointValues: tuple[int, int]
    NameValue: str
    MetresValue: float
    OwnerValue: Mapping[str, object]
    ParamOwner: Mapping[str, object]
    TextPosition: tuple[float, ...]
    SelectedLeader: int
    RouteCenter: bool
    DesignIntent: bool
