from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the complete pattern retains the ordered features and displays from the same ordinary part allocation
@DataClass(frozen=True, slots=True)
class PatPartGraph:
    StockValue: SeedStockGraph
    AxisValue: ArchiveNode
    PlaneValue: ArchiveNode
    AngleValue: DimensionGraph
    PatternValue: ArchiveNode
    DriverValues: tuple[DimensionGraph, ...]
    HeaderValues: tuple[ArchiveNode, ArchiveNode, ArchiveNode]

    # the ordinary archive walks the actual stock prefix followed by its two datums and patterned result
    @property
    def RootsValue(self) -> tuple[ArchiveNode, ...]:
        return (
            *self.StockValue.RootsValue,
            self.AxisValue,
            self.PlaneValue,
            self.PatternValue,
        )
