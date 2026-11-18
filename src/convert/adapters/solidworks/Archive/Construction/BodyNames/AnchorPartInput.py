from dataclasses import dataclass as DataClass
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)


# authored anchor families must remain explicit beside dimension presentation rather than inferred from matching initial solid geometry
@DataClass(frozen=True, slots=True)
class AnchorPartInput:
    KindValue: Literal["corner", "center"]
    DimensionsValue: RectDimInput
