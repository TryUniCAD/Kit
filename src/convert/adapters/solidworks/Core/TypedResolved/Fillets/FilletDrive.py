from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the driver retains the live parameter and its actual presentation and selector owners
@DataClass(frozen=True, slots=True)
class FilletDrive:
    ItemValue: ArchiveNode
    DisplayValue: ArchiveNode
    DimensionValue: ArchiveNode
    ParamValue: ArchiveNode
    RadiusValue: float
