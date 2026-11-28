from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# centered anchors must retain local construction geometry separately from the unchanged four edge body contour
@DataClass(frozen=True, slots=True)
class CenterGraph:
    CenterValue: ArchiveNode
    ExternalPoint: ArchiveNode
    DiagonalValues: tuple[ArchiveNode, ...]
    RelationValues: tuple[dict[str, object], ...]
    PointValues: tuple[ArchiveNode, ...]
    LineValues: tuple[ArchiveNode, ...]
