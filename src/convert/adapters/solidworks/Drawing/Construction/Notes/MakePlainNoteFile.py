from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawRoot import (
    MakeDrawRoot,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.NeedPlainNote import (
    NeedPlainNote,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.PutPlainNoteMut import (
    PutPlainNoteMut,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.CheckBlankInput import (
    CheckBlankInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.FinishDrawFile import (
    FinishDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankBuild import (
    MakeBlankBuild,
)
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.WritePlainNoteDef import (
    WritePlainNoteDef,
)


# a standalone note extends the same drawing model and container generation used for an empty sheet
def MakePlainNoteFile(
    InputValue: BlankDrawInput, *, DisplayGrid: bool = True
) -> DrawingFile:
    CheckBlankInput(InputValue)
    if type(CastValue(object, DisplayGrid)) is not bool:
        raise TypeError("drawing grid display requires an explicit boolean")
    SheetValue, NoteValue = NeedPlainNote(InputValue.DrawingValue)
    BlankValue = ReplaceValue(
        InputValue.DrawingValue, Sheets=(ReplaceValue(SheetValue, Notes=None),)
    )
    GraphValue = MakeDrawRoot(
        MakeBlankBuild(BlankValue, InputValue.OptionsValue),
        UseDrawingAnsi=InputValue.OptionsValue.StyleValue.StandardValue == 0,
    )
    PutPlainNoteMut(
        GraphValue,
        NoteValue,
        InputValue.UiSettings.VersionValue,
        InputValue.OptionsValue.StyleValue.LanguageId,
    )
    return FinishDrawFile(
        InputValue, GraphValue, WritePlainNoteDef, DisplayGrid=DisplayGrid
    )
