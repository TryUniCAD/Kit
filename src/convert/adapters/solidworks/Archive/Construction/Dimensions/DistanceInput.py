from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# native driving lengths and presentation choices must be explicit before any dimension or mate identity is consumed
@DataClass(frozen=True, slots=True)
class DistanceInput:
    ValueMetres: float
    DesignIntent: bool
    SelectedLeader: int

    # ordinary distance construction admits finite positive lengths and the exact native presentation input domains
    def __post_init__(self) -> None:
        if RequireScalar(self.ValueMetres) < 1e-14:
            raise ValueError(
                "driving distance must be at least one e minus fourteen metres"
            )
        if type(CastValue(object, self.DesignIntent)) is not bool:
            raise TypeError("distance design intent must be an authored boolean")
        if type(CastValue(object, self.SelectedLeader)) is not int or not -(
            1 << 31
        ) <= self.SelectedLeader < (1 << 31):
            raise ValueError("distance leader must be an authored signed integer")
