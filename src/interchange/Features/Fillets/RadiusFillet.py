from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef


# source selected constant fillets need independent live radius and tangency controls
@MakeDataClass(frozen=True, slots=True)
class RadiusFillet(FeatureDef):
    EdgeSelectionId: str
    RadiusParameterId: str
    WeightParameterId: str
    TangentChain: bool = True
    RollingBallCorners: bool = True

    # explicit roles prevent copied dimensions and ambiguous source selection bindings
    def __post_init__(self) -> None:
        if not all(
            isinstance(CastValue(object, Identity), str) and Identity.strip()
            for Identity in (
                self.EdgeSelectionId,
                self.RadiusParameterId,
                self.WeightParameterId,
            )
        ):
            raise ValueError(
                "radius fillet requires nonempty selection and parameter ids"
            )
        if self.RadiusParameterId == self.WeightParameterId:
            raise ValueError("radius fillet parameter roles must be distinct")
        if any(
            type(Value) is not bool
            for Value in (self.TangentChain, self.RollingBallCorners)
        ):
            raise ValueError(
                "radius fillet propagation and corner modes must be boolean"
            )
