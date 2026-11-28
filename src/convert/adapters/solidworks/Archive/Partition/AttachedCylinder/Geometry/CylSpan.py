from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)


# the attached cylinder owns two distinct axial stations in the original sketch frame
@DataClass(frozen=True, slots=True)
class CylSpan:
    NearValue: KPrismVector
    FarValue: KPrismVector
    AxisValue: KPrismVector
    RadialValue: KPrismVector
    RadiusValue: float
