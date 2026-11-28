from dataclasses import dataclass as DataClass

from interchange.brep.Topology.BrepTopology import BrepCoedge, BrepFace, BrepLoop


# each face in the resident profile owns one ordered outer loop and its actual edge uses
@DataClass(frozen=True, slots=True)
class PrismFaceLoop:
    FaceValue: BrepFace
    LoopValue: BrepLoop
    UsesValue: tuple[BrepCoedge, ...]
