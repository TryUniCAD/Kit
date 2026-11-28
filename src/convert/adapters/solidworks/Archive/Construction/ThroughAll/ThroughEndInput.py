from dataclasses import dataclass as DataClass
from typing import Literal, cast as CastValue


# termination without a distance must retain independent direction and actual archive version
@DataClass(frozen=True, slots=True)
class ThroughEndInput:
    ModeValue: Literal["through_all", "through_all_both"]
    IsReversed: bool
    VersionValue: int

    # invalid dimensional or version assumptions must fail before feature allocation
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("through all construction requires archive version 19000")
        if (
            self.ModeValue not in ("through_all", "through_all_both")
            or type(CastValue(object, self.IsReversed)) is not bool
        ):
            raise ValueError(
                "through all construction requires its actual termination and boolean direction"
            )
        if self.ModeValue == "through_all_both" and not self.IsReversed:
            raise ValueError(
                "the measured both direction profile requires its actual first direction reversal"
            )
