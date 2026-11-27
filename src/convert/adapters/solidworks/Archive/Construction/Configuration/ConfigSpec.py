from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# configuration naming and modification epochs belong to explicit document intent and retain their independent manager namespace
@DataClass(frozen=True, slots=True)
class ConfigSpec:
    NameValue: str
    Description: str
    UpdatedAt: int

    # malformed configuration intent must fail before feature initialization can allocate or mutate any owning graph
    def __post_init__(self) -> None:
        if not ReadStyleText(self.NameValue, "configuration name"):
            raise ValueError("configuration names must not be empty")
        _ = ReadStyleText(self.Description, "configuration description")
        if type(self.UpdatedAt) is not int or not 0 <= self.UpdatedAt <= 0xFFFFFFFF:
            raise ValueError("configuration update time must fit unsigned unix seconds")
