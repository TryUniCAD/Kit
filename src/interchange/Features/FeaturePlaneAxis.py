from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef
from interchange.Features.PlaneAxisLine import GetAxisLine
from interchange.geometry.Models.VectorSpace import SpaceVector


# two plane constraints need their selected owner order and an explicitly directed finite extent
@MakeDataClass(frozen=True, slots=True)
class PlaneAxis(FeatureDef):
    FirstPlaneSelectionId: str
    SecondPlaneSelectionId: str
    StartMm: SpaceVector
    EndMm: SpaceVector

    # invalid authored selections and segments must fail before they enter the neutral graph
    def __post_init__(self) -> None:
        Selections = (self.FirstPlaneSelectionId, self.SecondPlaneSelectionId)
        if (
            not all(
                isinstance(CastValue(object, Identity), str) and Identity.strip()
                for Identity in Selections
            )
            or self.FirstPlaneSelectionId == self.SecondPlaneSelectionId
        ):
            raise ValueError("plane axis requires two distinct nonempty selection ids")
        _ = GetAxisLine(self.StartMm, self.EndMm)
