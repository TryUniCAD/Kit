from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# angular history needs the actual hinge and two supports alongside its live dimension
@DataClass(frozen=True, slots=True)
class TiltOwner:
    HingeValue: ArchiveNode
    TopValue: ArchiveNode
    RightValue: ArchiveNode
    Dimension: ArchiveNode
    DriverValue: ArchiveNode
    AngleValue: float
