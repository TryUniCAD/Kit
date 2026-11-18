from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# origin composition must retain its actual point constraint and exclusive reference objects rather than serialize unrelated graph copies
@DataClass(frozen=True, slots=True)
class OriginGraph:
    ProfileValue: ArchiveNode
    SketchValue: ArchiveNode
    PointValue: ArchiveNode
    Constraint: ArchiveNode
    PlaneReference: ArchiveNode
