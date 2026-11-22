from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import (
    PatAngleStyle,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)


# explicit display choices cannot be inferred from neutral geometry or keyword captions
@DataClass(frozen=True, slots=True)
class PatPresentInput:
    AngleStyle: PatAngleStyle
    CountParamId: str
    PitchParamId: str
    StyleValues: tuple[PatDriveStyle, ...]
    AnnoValues: tuple[AnnoViewInput, ...]
    ActiveAnno: str | None
    ShownAnnos: tuple[str | None, ...]
