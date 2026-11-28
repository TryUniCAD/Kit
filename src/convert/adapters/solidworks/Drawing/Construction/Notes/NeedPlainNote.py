from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Validation.CheckDrawing import CheckDrawing


# the first note profile admits only standalone printable text on its actual unlinked sheet
def NeedPlainNote(DrawingValue: DrawingData) -> tuple[DrawingSheet, DrawingNote]:
    if (
        CheckDrawing(DrawingValue)
        or len(DrawingValue.Sheets) != 1
        or DrawingValue.ModelRefs
    ):
        raise ValueError("plain note construction requires one valid unlinked sheet")
    SheetValue = DrawingValue.Sheets[0]
    NotesValue = SheetValue.Notes
    if SheetValue.Views or NotesValue is None or len(NotesValue) != 1:
        raise ValueError("plain note construction requires exactly one standalone note")
    NoteValue = NotesValue[0]
    if not NoteValue.TextValue.isprintable() or any(
        Character in NoteValue.TextValue for Character in "<>"
    ):
        raise ValueError("plain note construction requires printable unformatted text")
    return SheetValue, NoteValue
