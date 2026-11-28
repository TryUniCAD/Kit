from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.BasicPbrInput import (
    BasicPbrInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.ClassicLook import (
    ClassicLook,
)


# the modeled part appearance retains the installation alias and starts ordered allocation on the part manager
@DataClass(frozen=True, slots=True)
class PartLookInput:
    DataDirectory: str
    ResourceName: str
    StartAppearanceId: int
    EmptyBomOnWire: bool
    MainRgb: tuple[int, int, int]
    HiddenLineRgb: tuple[int, int, int]
    LegacyMaterialName: str
    LegacySpecular: float
    ClassicValue: ClassicLook
    ShaderValue: BasicPbrInput
