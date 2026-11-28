from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the actual driver vertices preserve distinct values and presentation storage
@DataClass(frozen=True, slots=True)
class PatternDim:
    SlotName: str
    DisplayValue: ArchiveNode
    HandleValue: ArchiveNode
    DimensionValue: ArchiveNode
    ParameterValue: ArchiveNode
    NativeName: str
    LiveValue: int | float
    CacheValue: float
