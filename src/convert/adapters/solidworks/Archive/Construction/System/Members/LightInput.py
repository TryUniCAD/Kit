from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.System.Members.CheckLightInput import (
    CheckLightInput,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)


# explicit scene inputs prevent session defaults from becoming saved lighting seeds
@DataClass(frozen=True, slots=True)
class LightInput:
    KindValue: str
    NameValue: str
    ExternalName: str
    AmbientValue: float
    DiffuseValue: float
    SpecularValue: float
    ColourValue: int
    KeepInScene: bool
    EnabledInPv: bool
    UseCartesian: bool
    PvBrightness: float
    PvShadows: bool
    PvQuality: float
    DirectionValue: tuple[float, float, float] | None
    ShadowSoftness: float | None
    CreatedValue: FeatureInstant

    # invalid light semantics must fail before the shared model allocator is consumed
    def __post_init__(self) -> None:
        CheckLightInput(self)
