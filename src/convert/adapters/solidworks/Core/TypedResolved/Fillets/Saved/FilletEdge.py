from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the selected result records the actual historical edge rather than an index on the active rounded body
@DataClass(frozen=True, slots=True)
class FilletEdge:
    RefValue: ArchiveNode
    NativeIndex: int
    FaceIds: tuple[int, ...]
    Endpoints: tuple[tuple[float, float, float], tuple[float, float, float]]
