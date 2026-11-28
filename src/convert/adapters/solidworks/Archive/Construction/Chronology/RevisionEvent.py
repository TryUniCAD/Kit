from dataclasses import dataclass as DataClass
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# explicit revision semantics prevent independent source events from being replaced by the output clock
@DataClass(frozen=True, slots=True)
class RevisionEvent:
    OperationValue: Literal["created", "modified"]
    UserName: str
    CompanyName: str
    EventAt: int
    CommentText: str

    # malformed events must fail before attribution indices or archive objects are allocated
    def __post_init__(self) -> None:
        if self.OperationValue not in ("created", "modified"):
            raise ValueError("revision operation is outside the mapped ordinary scope")
        if type(self.EventAt) is not int or not 946684800 <= self.EventAt < 4102444800:
            raise ValueError("revision event requires explicit modern wall seconds")
        for NameValue, TextValue in (
            ("revision user", self.UserName),
            ("revision company", self.CompanyName),
            ("revision comment", self.CommentText),
        ):
            _ = ReadStyleText(TextValue, NameValue)
