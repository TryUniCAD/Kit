from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# empty appearance data still owns allocation history that readers must retain explicitly
@DataClass(frozen=True, slots=True)
class AppearanceState:
    ManagerOnWire: bool
    NextAppearanceId: int

    # malformed allocator state must fail before an empty manager acquires semantic admission
    def __post_init__(self) -> None:
        if type(CastValue(object, self.ManagerOnWire)) is not bool:
            raise TypeError("drawing appearance presence must be a boolean")
        if type(CastValue(object, self.NextAppearanceId)) is not int:
            raise TypeError("drawing appearance allocator must be an integer")
        if not 0 <= self.NextAppearanceId <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("drawing appearance allocator exceeds unsigned64 storage")
