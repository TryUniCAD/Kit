from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# occurrence index rows carry the local identity and the linked physical file stem
@DataClass(frozen=True, slots=True)
class KeywordRef:
    IdValue: int
    NameValue: str
    FileStem: str

    # the reference type derives from a file stem while the visible occurrence name has its own owner
    def __post_init__(self) -> None:
        if type(self.IdValue) is not int or not 1 <= self.IdValue <= 0x7FFFFFFF:
            raise ValueError("keyword occurrence id must be a positive signed integer")
        _ = ReadStyleText(self.NameValue, "keyword occurrence name")
        StemValue = ReadStyleText(self.FileStem, "keyword linked file stem")
        if not StemValue or "/" in StemValue or "\\" in StemValue:
            raise ValueError("keyword reference requires the linked file stem")
