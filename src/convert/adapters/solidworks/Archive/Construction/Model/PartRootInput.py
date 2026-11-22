from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# fresh part roots need explicit names and target version before any native owner exists
@DataClass(frozen=True, slots=True)
class PartRootInput:
    NameValue: str
    HatchName: str
    VersionValue: int

    # invalid provenance must fail before native constructor bookkeeping can be published
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("part root construction requires archive version 19000")
        for NameValue in (self.NameValue, self.HatchName):
            if (
                type(CastValue(object, NameValue)) is not str
                or not NameValue
                or "\x00" in NameValue
            ):
                raise ValueError(
                    "part and hatch names must be nonempty strings without null characters"
                )
