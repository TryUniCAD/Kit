from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeTextFields import (
    MakeTextFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteParagraph import (
    MakeParagraph,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteTokens import (
    MakeNoteTokens,
)
from interchange.document.Models.Drawing.DrawingNote import DrawingNote


# generic note text reuses the native text base and supplies authored placement together with its ordered character owners
def MakeNoteText(
    NoteValue: DrawingNote, StyleValue: Mapping[str, object]
) -> ArchiveNode:
    Position = NoteValue.PositionValue
    FieldsValue = MakeTextFields(21)
    FieldsValue.update(
        {
            "f08": NoteValue.TextValue,
            "f20": StyleValue["f1c"],
            "f38": MakePoint(XValue=Position.x, YValue=Position.y, ZValue=Position.z),
            "f158": MakeNoteTokens(NoteValue.TextValue, StyleValue),
            "f160": (1 << 0) | (1 << 10) | (1 << 16) | (1 << 17) | (1 << 18),
            "f170": None,
            "f188": MakeParagraph(StyleValue, False),
        }
    )
    return ArchiveNode(RuntimeClass("moGenericText_c", 1), FieldsValue)
