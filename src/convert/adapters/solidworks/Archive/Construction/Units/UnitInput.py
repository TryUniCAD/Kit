from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KAngleCodes,
    KLengthCodes,
    KMassCodes,
    KSystemCodes,
)


# semantic unit settings must be explicit before any model or annotation formats are constructed
@DataClass(frozen=True, slots=True)
class UnitInput:
    LengthUnit: str
    AngleUnit: str
    UnitSystem: str
    DecimalPlaces: int
    MassUnit: str | None = None

    # unsupported names or precision must fail without native preference lookup or clamping
    def __post_init__(self) -> None:
        for NameValue, Choices in (
            (self.LengthUnit, KLengthCodes),
            (self.AngleUnit, KAngleCodes),
            (self.UnitSystem, KSystemCodes),
        ):
            if (
                type(CastValue(object, NameValue)) is not str
                or NameValue not in Choices
            ):
                raise ValueError("unsupported semantic native unit name")
        if (
            type(CastValue(object, self.DecimalPlaces)) is not int
            or not 0 <= self.DecimalPlaces <= 16
        ):
            raise ValueError(
                "native unit precision must be an integer from zero through sixteen"
            )
        if self.UnitSystem == "custom":
            if (
                (self.LengthUnit, self.AngleUnit) != ("mm", "degree")
                or type(CastValue(object, self.MassUnit)) is not str
                or self.MassUnit not in KMassCodes
            ):
                raise ValueError(
                    "custom units require millimetres degrees and an explicit gram or kilogram mass"
                )
        elif self.MassUnit is not None:
            raise ValueError("an explicit mass unit requires the custom system")
