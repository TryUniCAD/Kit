from dataclasses import dataclass as DataClass

from interchange.brep.Topology.BrepModel import BrepModel


# physical ownership accompanies the decoded active payload through the public projection
@DataClass(frozen=True, slots=True)
class WarmChmfBody:
    BrepValue: BrepModel
    PayloadHash: str
    MarkIds: tuple[int, ...]
    BodySlot: int
    EdgeSlot: int
    FaceSlot: int
