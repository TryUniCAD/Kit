from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the anchor retains actual selected origin point relation and external ownership instead of reconstructed numeric references
@DataClass(frozen=True, slots=True)
class CornerGraph:
    ExternalPoint: ArchiveNode
    ExternalEntity: ArchiveNode
    WrapperValue: ArchiveNode
    SelectionValue: ArchiveNode
    RelationValue: dict[str, object]
    PointValues: tuple[ArchiveNode, ...]
