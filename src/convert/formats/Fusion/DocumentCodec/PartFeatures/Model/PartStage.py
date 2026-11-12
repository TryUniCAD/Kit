from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


@MakeDataClass(frozen=True, slots=True)
class PartStage:
    Feature: KPartFeature
    Before: PrismSolid
    After: PrismSolid
    Operations: tuple[int, ...]
    StateId: int
    FamilyIndex: int
