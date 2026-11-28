from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisPick import (
    AxisPick,
)


# stored endpoints and their actual parent plane wrappers belong to one axis vertex
@MakeDataClass(frozen=True, slots=True)
class PrismAxis:
    NodeValue: ArchiveNode
    DataValue: ArchiveNode
    NameValue: ArchiveNode
    PicksValue: tuple[AxisPick, AxisPick]
    StartValue: tuple[float, float, float]
    EndValue: tuple[float, float, float]
