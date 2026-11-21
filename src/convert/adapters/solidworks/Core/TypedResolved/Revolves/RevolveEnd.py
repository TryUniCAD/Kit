from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from interchange.Features.RevolveSpan import GetAngleSpan


# sweep bounds remain derived from the actual editable angular dimensions
@Dataclass(frozen=True, slots=True)
class RevolveEnd:
    ModeValue: str
    AlongValue: RevolveAngle
    AgainstValue: RevolveAngle | None

    # cached and reconstructed bodies need the same interval around the effective axis
    @property
    def IntervalValue(self) -> tuple[float, float]:
        AgainstValue = self.AgainstValue
        return GetAngleSpan(
            self.AlongValue.RadiansValue,
            None if AgainstValue is None else AgainstValue.RadiansValue,
            self.ModeValue,
        )
