from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)


# explicit ordered scene entries prevent a fixed session default vector from entering construction
@DataClass(frozen=True, slots=True)
class MemberInput:
    NotesValue: NotesInput
    LightValues: tuple[LightInput, ...]

    # member identities must be unambiguous while external light identifiers may legitimately repeat
    def __post_init__(self) -> None:
        if (
            type(self.NotesValue) is not NotesInput
            or type(self.LightValues) is not tuple
            or not self.LightValues
            or any(
                type(ValueInput) is not LightInput for ValueInput in self.LightValues
            )
        ):
            raise TypeError(
                "members require a note pair and an explicit ordered typed scene"
            )
        NamesValue = (
            self.NotesValue.HeadName,
            self.NotesValue.EndName,
            *(ValueInput.NameValue for ValueInput in self.LightValues),
        )
        if len(set(NamesValue)) != len(NamesValue):
            raise ValueError(
                "member captions must be distinct within the part namespace"
            )
