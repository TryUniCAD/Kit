from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# the solved plane and its separate display frame retain their actual geometric owners
@DataClass(frozen=True, slots=True)
class AngleGeometry:
    PlaneValue: PlaneFrame
    BordersValue: tuple[float, float, float, float]
    NameCorner: KDatumVector
    DimensionValue: PlaneFrame
    ShiftValue: KDatumVector
    WitnessValues: tuple[KDatumVector, KDatumVector, KDatumVector]
    LabelValue: KDatumVector
    RadiusValue: float
    Separation: float
