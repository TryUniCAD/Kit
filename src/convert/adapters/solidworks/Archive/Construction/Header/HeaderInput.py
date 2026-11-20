from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# fresh part header provenance must be supplied independently of saved document names clocks or license metadata
@DataClass(frozen=True, slots=True)
class HeaderInput:
    AuthorName: str
    CompanyName: str
    CommentText: str
    CreatedAt: int
    ModifiedAt: int
    UpdatedAt: int

    # invalid text epochs and temporal ordering must fail before any native revision record is constructed
    def __post_init__(self) -> None:
        for NameValue, TextValue in (
            ("author", self.AuthorName),
            ("company", self.CompanyName),
            ("comment", self.CommentText),
        ):
            _ = ReadStyleText(TextValue, NameValue)
        if any(
            type(TimeValue) is not int or not 0 <= TimeValue <= 0xFFFFFFFF
            for TimeValue in (self.CreatedAt, self.ModifiedAt, self.UpdatedAt)
        ):
            raise ValueError("header times must fit unsigned unix seconds")
        if self.ModifiedAt < self.CreatedAt:
            raise ValueError("header modification time precedes document creation")
