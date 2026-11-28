from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a translated supporting plane owns the frame and distance used by its dependent sketch
@DataClass(frozen=True, slots=True)
class OffsetGraph:
    FeatureValue: ArchiveNode
    DatumValue: ArchiveNode
    FrameValue: PlaneFrame
    DistanceValue: DimensionGraph
