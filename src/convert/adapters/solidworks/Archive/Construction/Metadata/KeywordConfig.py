from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# keyword configurations must refer to actual generated configuration identities and explicitly supplied names and material text
@DataClass(frozen=True, slots=True)
class KeywordConfig:
    IdValue: int
    NameValue: str
    MaterialValue: str

    # malformed configuration identity or text must fail before an xml document can conceal a graph mismatch
    def __post_init__(self) -> None:
        if type(self.IdValue) is not int or not 0 <= self.IdValue <= 0x7FFFFFFF:
            raise ValueError(
                "keyword configuration id must be a nonnegative signed integer"
            )
        _ = ReadStyleText(self.NameValue, "keyword configuration name")
        _ = ReadStyleText(self.MaterialValue, "keyword material text")
