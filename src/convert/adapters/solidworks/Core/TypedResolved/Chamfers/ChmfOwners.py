from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)


# a local chamfer retains its two driver chains and ordered references before any physical interpretation
@DataClass(frozen=True, slots=True)
class ChmfOwners:
    StockValue: ArchiveNode
    FeatureValue: ArchiveNode
    AtomValue: ArchiveNode
    SelectedRef: ArchiveNode
    DetachedRef: ArchiveNode
    Distance: ChmfDriver
    AngleValue: ChmfDriver
    Controllers: tuple[ArchiveNode, ...]
