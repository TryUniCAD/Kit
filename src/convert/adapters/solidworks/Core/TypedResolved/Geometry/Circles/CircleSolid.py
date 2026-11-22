from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.Partition.PartMass import PartMass
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Records.RecordTopology import TopologyCounts


# the cold solid and its analytic measures share the same actual typed cylinder
@DataClass(frozen=True, slots=True)
class CircleSolid:
    BrepValue: BrepModel
    TopologyValue: TopologyCounts
    MassValue: PartMass
