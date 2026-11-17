from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)


# the typed projection carries design intent independently of the legacy string reader
@DataClass(frozen=True, slots=True)
class PlanarMate:
    MateId: int
    NameValue: str
    KindValue: str
    ClassName: str
    AlignmentCode: int
    Endpoints: tuple[PlanarEndpoint, PlanarEndpoint]
    DistanceValue: float | None
