from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Records.RecordTopology import TopologyCounts
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)


# generated neutral geometry must remain distinct from absent native payload bytes and persisted kernel identities
@DataClass(frozen=True, slots=True)
class PartGeometry:
    BrepValue: BrepModel
    TopologyValue: TopologyCounts
    EvidenceValue: Mapping[str, object]
    ColdValue: ColdOutput | None = None
