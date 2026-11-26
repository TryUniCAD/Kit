from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef


# authored extents can follow support edits through independently owned signed length parameters
@MakeDataClass(frozen=True, slots=True)
class BoundPlaneAxis(FeatureDef):
    FirstPlaneSelectionId: str
    SecondPlaneSelectionId: str
    StartParameterId: str
    EndParameterId: str

    # each station and each plane needs its own role so editors can move them independently
    def __post_init__(self) -> None:
        Selections = (self.FirstPlaneSelectionId, self.SecondPlaneSelectionId)
        Parameters = (self.StartParameterId, self.EndParameterId)
        if (
            not all(
                isinstance(CastValue(object, Identity), str) and Identity.strip()
                for Identity in (*Selections, *Parameters)
            )
            or len(set(Selections)) != 2
            or len(set(Parameters)) != 2
        ):
            raise ValueError(
                "bound plane axis requires distinct plane and extent roles"
            )
