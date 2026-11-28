from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# each provisional stock must share its identity across its profile driver and selected atom owners
@DataClass(frozen=True, slots=True)
class StockBossGraph:
    FeatureValue: ArchiveNode
    ProfileValue: ProfileGraph
    DriverValue: DimensionGraph
    AtomValue: ArchiveNode
