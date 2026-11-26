from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeDimension


# the forward depth must retain its actual parameter dimension and display identities together
@DataClass(frozen=True, slots=True)
class DepthOwner:
    Parameter: ArchiveNode
    Dimension: ArchiveNode
    HandleValue: ArchiveNode
    DisplayValue: ArchiveNode
    DepthValue: NativeDimension
