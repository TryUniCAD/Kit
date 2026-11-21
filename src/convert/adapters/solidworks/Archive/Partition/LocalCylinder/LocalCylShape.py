from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CylRim import CylRim
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepTopology import BrepFace


# a single portable cylinder must identify the two actual stations before allocating wire records
@DataClass(frozen=True, slots=True)
class LocalCylShape:
    SideFace: BrepFace
    MantleValue: CylinderSurface
    FarRim: CylRim
    NearRim: CylRim
