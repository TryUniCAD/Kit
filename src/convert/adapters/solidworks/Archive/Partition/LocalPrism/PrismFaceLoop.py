from dataclasses import dataclass as DataClass

from interchange.brep.Topology.BrepTopology import BrepCoedge, BrepFace, BrepLoop


# each directed trim binds its own face and actual edge occurrences
@DataClass(frozen=True, slots=True)
class PrismFaceLoop:
    FaceValue: BrepFace
    LoopValue: BrepLoop
    UsesValue: tuple[BrepCoedge, ...]
