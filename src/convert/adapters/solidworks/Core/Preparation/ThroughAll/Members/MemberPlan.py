from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import (
    MemberInput,
)


# source correspondence retains semantic identities separately from newly allocated member nodes
@DataClass(frozen=True, slots=True)
class MemberPlan:
    InputValue: MemberInput
    NoteIds: tuple[str, str]
    LightIds: tuple[str, ...]
