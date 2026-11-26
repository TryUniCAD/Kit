from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# completed boss composition must retain active inactive and transient dimensions as actual objects while exposing its shared profile and end owner
@DataClass(frozen=True, slots=True)
class ExtrusionGraph:
    FeatureValue: ArchiveNode
    ProfileValue: ProfileGraph
    EndValue: ArchiveNode
    DimensionsValue: tuple[DimensionGraph, ...]
    FromValue: DimensionGraph
