from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)


# optional assembly presentation needs explicit typed ownership before the shared allocator runs
def CheckAsmMembers(
    NamesValue: tuple[str, ...],
    LightValues: tuple[LightInput, ...],
    NotesValue: NotesInput | None,
    HasEmptyExplodedView: bool,
) -> None:
    if type(LightValues) is not tuple or any(
        type(LightValue) is not LightInput for LightValue in LightValues
    ):
        raise TypeError("assembly lighting requires ordered typed light inputs")
    LightNames = {LightValue.NameValue for LightValue in LightValues}
    if len(LightNames) != len(LightValues) or LightNames.intersection(NamesValue):
        raise ValueError("assembly light names must be distinct system captions")
    if NotesValue is not None:
        if type(NotesValue) is not NotesInput:
            raise TypeError("assembly notes require typed empty pair input")
        if not {NotesValue.HeadName, NotesValue.EndName}.isdisjoint(
            (*NamesValue, *LightNames)
        ):
            raise ValueError("assembly note captions must be distinct system names")
    if type(HasEmptyExplodedView) is not bool:
        raise TypeError("assembly exploded view presence requires a boolean")
