from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef
from interchange.Features.FeatureDistExt import DistanceExtrude


# modifying distance features retain live extent controls and explicit body operands
@MakeDataClass(frozen=True, slots=True)
class DistanceCut(FeatureDef):
    Extrusion: DistanceExtrude
    TargetBodyIds: tuple[str, ...]

    # body operands must remain explicit and unique across parameter edits
    def __post_init__(self) -> None:
        if not isinstance(CastValue(object, self.Extrusion), DistanceExtrude):
            raise ValueError("distance cut requires a live distance extrusion")
        if (
            not isinstance(CastValue(object, self.TargetBodyIds), tuple)
            or not self.TargetBodyIds
        ):
            raise ValueError("distance cut requires explicit body operands")
        if not all(
            isinstance(CastValue(object, Identity), str) and Identity.strip()
            for Identity in self.TargetBodyIds
        ) or len(set(self.TargetBodyIds)) != len(self.TargetBodyIds):
            raise ValueError(
                "distance cut body operands must be distinct nonempty identities"
            )
