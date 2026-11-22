from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the full circle retains its same actual arc and point owners for later relations and dimension references
@DataClass(frozen=True, slots=True)
class CircleGraph:
    SketchValue: ArchiveNode
    ArcValue: ArchiveNode
    CenterValue: ArchiveNode
    MarkerValue: ArchiveNode

    # the shared sketch wrapper exposes its actual ordered position objects
    @property
    def PointValues(self) -> tuple[ArchiveNode, ...]:
        return self.CenterValue, self.MarkerValue

    # existing straight segment consumers must see the actual empty line array
    @property
    def LineValues(self) -> tuple[ArchiveNode, ...]:
        return ()
