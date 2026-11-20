from dataclasses import dataclass as DataClass
from typing import cast as CastValue


# fresh definitions need explicit presentation values before the native owners are constructed
@DataClass(frozen=True, slots=True)
class ModelDefInput:
    DraftingStandard: str
    DisplayBits: tuple[int, ...]
    Tessellation: tuple[int, int, int, bool]
    Preference7a: bool
    JournalName: str
    VersionValue: int

    # model display flags must be validated before packing them into signed archive words
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("fresh model Definition requires archive version 19000")
        if self.DraftingStandard not in (
            "moANSI_c",
            "moISO_c",
            "moBS_c",
            "moDIN_c",
            "moJIS_c",
            "moGB_c",
            "moGOST_c",
        ):
            raise ValueError("unsupported SOLIDWORKS drafting standard")
        if any(
            type(CastValue(object, Value)) is not int or not 0 <= Value < 64
            for Value in self.DisplayBits
        ):
            raise ValueError("SOLIDWORKS display flags require bit positions below 64")
        if (
            not isinstance(CastValue(object, self.Tessellation), tuple)
            or len(self.Tessellation) != 4
        ):
            raise ValueError("SOLIDWORKS tessellation requires four preference values")
        if any(
            type(CastValue(object, Value)) is not int or not 0 <= Value < 2**31
            for Value in self.Tessellation[:3]
        ):
            raise ValueError(
                "SOLIDWORKS tessellation values require nonnegative signed integers"
            )
        if (
            type(CastValue(object, self.Tessellation[3])) is not bool
            or type(CastValue(object, self.Preference7a)) is not bool
        ):
            raise TypeError("SOLIDWORKS document preference switches require booleans")
        if (
            type(CastValue(object, self.JournalName)) is not str
            or not self.JournalName
            or "\x00" in self.JournalName
        ):
            raise ValueError(
                "SOLIDWORKS journal name must be nonempty text without nulls"
            )
