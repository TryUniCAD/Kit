from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.Partition.CircularPartition import CylinderData
from interchange.brep.Topology.BrepModel import BrepModel


# reuse the validated cylinder only for the same active partition
@DataClass(frozen=True, slots=True)
class AttachedCylinder:
    BodyValue: BrepModel
    ShapeValue: CylinderData
    DigestValue: str
