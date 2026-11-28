from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)


# pattern travel and its dimension witnesses use the same measured local direction geometry
@DataClass(frozen=True, slots=True)
class PatDirLine:
    PointValue: KDatumVector
    DirectionValue: KDatumVector
    SpanValue: float
    RoleValue: int = 0
