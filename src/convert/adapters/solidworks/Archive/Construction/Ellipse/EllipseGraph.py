from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the inline ellipse and owned points need separate typed identities through archive allocation
@DataClass(frozen=True, slots=True)
class EllipseGraph:
    SketchValue: ArchiveNode
    PointValues: tuple[ArchiveNode, ...]
    SegmentValue: ArchiveNode

    # shared profile consumers must see the ellipse sketch without any straight segments
    @property
    def LineValues(self) -> tuple[ArchiveNode, ...]:
        return ()
