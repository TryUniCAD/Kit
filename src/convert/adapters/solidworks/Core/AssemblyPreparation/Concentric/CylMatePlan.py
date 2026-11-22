from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.CylMateEnd import (
    CylMateEnd,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from interchange.assembly.MateConstraint import MateConstraint
from interchange.brep.Topology.BrepTopology import BrepFace


# assembly construction needs distinct occurrence and selection orders with the actual source and kernel owners
@DataClass(frozen=True, slots=True)
class CylMatePlan:
    ModelValue: AsmRootData
    MateValue: MateConstraint
    CandidateValue: PartCandidate
    NeutralFace: BrepFace
    FaceValue: CylFaceBuild
    Placements: tuple[OccurrenceIn, OccurrenceIn]
    EndsValue: tuple[CylMateEnd, CylMateEnd]
    EndIndexes: tuple[int, int]
    MateInput: CylMateIn
