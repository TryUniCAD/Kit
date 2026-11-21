from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# active wall intent must remain tied to the actual native display chain
@DataClass(frozen=True, slots=True)
class ThinWallOwner:
    DisplayValue: ArchiveNode
    HandleValue: ArchiveNode
    DimensionValue: ArchiveNode
    ParameterValue: ArchiveNode
    NameValue: str
    MetresValue: float
