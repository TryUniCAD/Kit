from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# actual native view quality grid and command group inputs replace separately saved ui words
@DataClass(frozen=True, slots=True)
class PartUiInput:
    HlrQualityCode: int
    DisplayGrid: bool
    DefaultCommandGroup: str

    # this ordinary part profile excludes unknown quality values grid masks and command groups
    def __post_init__(self) -> None:
        if type(
            CastValue(object, self.HlrQualityCode)
        ) is not int or self.HlrQualityCode not in (0, 1):
            raise ValueError(
                "part ui hidden line quality is outside the proven profile"
            )
        if type(CastValue(object, self.DisplayGrid)) is not bool:
            raise TypeError("part ui grid visibility requires a boolean")
        if type(
            CastValue(object, self.DefaultCommandGroup)
        ) is not str or self.DefaultCommandGroup not in ("none", "features"):
            raise ValueError("part ui command group is outside the proven profile")
