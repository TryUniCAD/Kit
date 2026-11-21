from dataclasses import dataclass as DataClass
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)


# the part self state explicitly requests the independently modeled constructor appearance
@DataClass(frozen=True, slots=True)
class PartSelfView:
    StateName: str
    AppearanceValue: Literal["constructor"] | PartLookInput
