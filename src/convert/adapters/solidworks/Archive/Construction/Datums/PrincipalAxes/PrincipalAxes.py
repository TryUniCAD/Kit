from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxis import (
    PrincipalAxis,
)


# three independently selectable principal lines share one real modeled origin
@DataClass(frozen=True, slots=True)
class PrincipalAxes:
    OriginName: str
    OriginShown: bool
    AxisValues: tuple[PrincipalAxis, ...]
