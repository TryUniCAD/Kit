from dataclasses import dataclass as DataClass

from downstream.lighting.CheckAmbientInput import (
    CheckAmbientInput,
)


# one authored ambient light has independent display identity and rendering inputs rather than application defaults
@DataClass(frozen=True, slots=True)
class AmbientInput:
    NameValue: str
    ExternalName: str
    AmbientValue: float
    DiffuseValue: float
    SpecularValue: float
    ColourValue: int

    # invalid authored inputs must fail before persistent allocation or owner attachment
    def __post_init__(self) -> None:
        CheckAmbientInput(
            self.NameValue,
            self.ExternalName,
            self.AmbientValue,
            self.DiffuseValue,
            self.SpecularValue,
            self.ColourValue,
        )
