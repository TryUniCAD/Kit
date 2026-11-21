from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite


# physical assignment binds a modeled density to a catalog and material name supplied by the model
@DataClass(frozen=True, slots=True)
class PartMaterialInput:
    CatalogValue: str
    NameValue: str
    DensityValue: float

    # fresh material identity tokens must already belong to one unambiguous positive density assignment
    def __post_init__(self) -> None:
        if any(
            type(TextValue) is not str
            or not TextValue
            or not TextValue.isprintable()
            or "|" in TextValue
            for TextValue in (self.CatalogValue, self.NameValue)
        ) or any(Value in self.CatalogValue for Value in ("/", "\\")):
            raise ValueError("part material requires a catalog key and material name")
        if (
            isinstance(self.DensityValue, bool)
            or not IsFinite(self.DensityValue)
            or self.DensityValue <= 0
        ):
            raise ValueError("part material density must be positive and finite")

    # the measured two-token identity keeps its original catalog and material spelling
    @property
    def IdentityValue(self) -> str:
        return f"{self.CatalogValue}|{self.NameValue}"
