from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# retained typed identities keep endpoint indices distinct from archive references and creation identifiers
@DataClass(frozen=True, slots=True)
class PolygonGraph:
    SketchValue: ArchiveNode
    PointValues: tuple[ArchiveNode, ...]
    LineValues: tuple[ArchiveNode, ...]
