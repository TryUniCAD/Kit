from collections.abc import Mapping
from dataclasses import dataclass as DataClass


# the local circle view retains its actual arc centre and driving identities even when marker scans are empty
@DataClass(frozen=True, slots=True)
class LocalCircle:
    CenterValue: tuple[float, float]
    RadiusValue: float
    ArcMark: int
    CenterMark: int
    ModeValue: str | None
    DriverName: str | None
    OwnerValue: Mapping[str, object]
