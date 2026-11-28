from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import (
    StockBossGraph,
)


# all streams must share the same fresh root members and persistent allocator
@DataClass(frozen=True, slots=True)
class TwoStockGraph:
    SystemValue: PartSystem
    BossValues: tuple[StockBossGraph, StockBossGraph]
    CutValue: CutGraph
    Allocator: PersistentIds

    # the resolved archive must preserve the sketch and operation order of each independent producer
    @property
    def RootValues(self) -> tuple[ArchiveNode, ...]:
        return (
            *self.SystemValue.FeatureValues,
            *(
                NodeValue
                for BossValue in self.BossValues
                for NodeValue in (
                    BossValue.ProfileValue.ProfileValue,
                    BossValue.FeatureValue,
                )
            ),
            self.CutValue.ProfileValue.ProfileValue,
            self.CutValue.FeatureValue,
        )
