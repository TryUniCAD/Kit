from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# kernel bookkeeping needs the actual linked body producer atom and creation event
@DataClass(frozen=True, slots=True)
class LocalBodyOwner:
    FeatureName: str
    FeatureId: int
    AtomId: int
    BodyStamp: int

    # the local integer and unicode attributes have independent typed wire domains
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.FeatureName)) is not str
            or not self.FeatureName
            or not self.FeatureName.isprintable()
        ):
            raise ValueError("local body owner needs its actual producer name")
        if any(
            type(Value) is not int or not 0 < Value < (1 << 31)
            for Value in (self.FeatureId, self.AtomId, self.BodyStamp)
        ):
            raise ValueError("local body owner identifiers are out of range")
