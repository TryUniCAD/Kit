from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    KStockBounds,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import (
    StockBossGraph,
)


# later pattern features need the same root allocator and managed seed result
@DataClass(frozen=True, slots=True)
class SeedStockGraph:
    SystemValue: PartSystem
    SettingsValue: PartBuildInput
    Allocator: PersistentIds
    PlateValue: StockBossGraph
    SeedValue: StockBossGraph
    BoundsValue: KStockBounds

    # native rendering needs the distinct sketch and boss rows in creation order
    @property
    def RootsValue(self) -> tuple[ArchiveNode, ...]:
        return (
            *self.SystemValue.FeatureValues,
            self.PlateValue.ProfileValue.ProfileValue,
            self.PlateValue.FeatureValue,
            self.SeedValue.ProfileValue.ProfileValue,
            self.SeedValue.FeatureValue,
        )
