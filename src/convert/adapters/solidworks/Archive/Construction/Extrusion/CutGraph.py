from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the ordinary cut retains the actual profile and its single live depth display
@DataClass(frozen=True, slots=True)
class CutGraph:
    FeatureValue: ArchiveNode
    ProfileValue: ProfileGraph
    EndValue: ArchiveNode
    DepthValue: DimensionGraph | None
