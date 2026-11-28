from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxis import (
    PrismAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# axis projection and shape admission must consume the same linked archive objects
@MakeDataClass(frozen=True, slots=True)
class PrismAxes:
    LinkValue: NativeLink
    AxesValue: tuple[PrismAxis, PrismAxis, PrismAxis]
    MembersValue: frozenset[ArchiveNode]
