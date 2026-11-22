from dataclasses import dataclass as DataClass

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# analytic measures remain attached to the particular reconstructed closed solid
@DataClass(frozen=True, slots=True)
class ColdSolid:
    BrepValue: BrepModel
    VolumeValue: float
    AreaValue: float
    BoundsValue: BoundingBox
    CenterValue: SpaceVector
