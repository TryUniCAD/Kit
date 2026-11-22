from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinWallOwner import (
    ThinWallOwner,
)


# the independent angular and wall owners must survive as one actual thin feature
@DataClass(frozen=True, slots=True)
class ThinRevOwner:
    SweepValue: RevolveOwner
    ModeValue: str
    WallValues: tuple[ThinWallOwner, ...]
    MeridianValue: tuple[tuple[float, float], ...]
