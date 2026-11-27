from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef


# face offsets retain the exact selected face and body independently of their signed distance control
@MakeDataClass(frozen=True, slots=True)
class FaceOffset(FeatureDef):
    TargetBodyId: str
    FaceSelectionId: str
    DistanceParamId: str

    # each live operand must remain an explicit nonempty identity through serialization
    def __post_init__(self) -> None:
        if not all(
            isinstance(CastValue(object, Identity), str) and Identity.strip()
            for Identity in (
                self.TargetBodyId,
                self.FaceSelectionId,
                self.DistanceParamId,
            )
        ):
            raise ValueError("face offset operand identities must be nonempty text")
