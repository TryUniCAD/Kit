from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the driving parameter value retaining handle and display must remain independently owned actual graph nodes
@DataClass(frozen=True, slots=True)
class DimensionGraph:
    ParameterValue: ArchiveNode
    DimensionValue: ArchiveNode
    HandleValue: ArchiveNode
    DisplayValue: ArchiveNode
