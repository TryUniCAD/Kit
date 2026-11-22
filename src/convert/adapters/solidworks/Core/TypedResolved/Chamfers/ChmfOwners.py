from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)


# a local chamfer retains the active slot chains and ordered references before any physical interpretation
@DataClass(frozen=True, slots=True)
class ChmfOwners:
    StockValue: ArchiveNode
    FeatureValue: ArchiveNode
    AtomValue: ArchiveNode
    SelectedRef: ArchiveNode
    DetachedRef: ArchiveNode
    Distance: ChmfDriver
    AngleValue: ChmfDriver | None
    Controllers: tuple[ArchiveNode, ...]
    ModeWord: int = 1
    SecondValue: ChmfDriver | None = None

    # parameter projection and map checks must follow the actual feature slot order
    @property
    def DriversValue(self) -> tuple[ChmfDriver, ...]:
        Secondary = self.AngleValue or self.SecondValue
        return (self.Distance,) if Secondary is None else (self.Distance, Secondary)
