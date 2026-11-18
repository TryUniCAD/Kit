from dataclasses import dataclass as DataClass
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)


# pocket history retains the actual first boss and its separately driven circular cut
@DataClass(frozen=True, slots=True)
class PocketPlan:
    BossValue: BlindPlan
    SketchName: str
    FeatureName: str
    CircleValue: CircleInput
    EndValue: BossEndInput
    RadialMode: Literal["radius", "diameter"] | None
