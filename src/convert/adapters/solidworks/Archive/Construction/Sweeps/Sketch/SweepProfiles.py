from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the sweep owns separate live sketches and their actually installed editable drivers
@DataClass(frozen=True, slots=True)
class SweepProfiles:
    SectionValue: ArchiveNode
    PathValue: ArchiveNode
    DiameterValue: DimensionGraph
    RadiusValue: DimensionGraph
