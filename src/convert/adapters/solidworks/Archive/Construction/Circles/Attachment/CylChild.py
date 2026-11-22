from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# a mate must receive the constructed child and its actual transient lateral face tag together
@DataClass(frozen=True, slots=True)
class CylChild:
    CandidateValue: PartCandidate
    FaceTag: int
