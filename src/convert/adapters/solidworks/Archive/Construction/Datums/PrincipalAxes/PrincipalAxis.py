from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)


# a neutral principal line owns its explicit name and signed world carrier
@DataClass(frozen=True, slots=True)
class PrincipalAxis:
    NameValue: str
    OriginValue: KDatumVector
    DirectionValue: KDatumVector
    IsVisible: bool
