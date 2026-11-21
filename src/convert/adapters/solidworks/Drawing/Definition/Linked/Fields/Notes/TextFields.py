from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.ParagraphFields import (
    KNoteParagraphFields,
)

# generic text retains actual object list and display owner aliases plus the mandatory embedded paragraph format
KNoteTextFields = MappingProxyType(
    {
        "moGenericText_c": GateNote(
            (
                NativeField("Base", "moDimText_c"),
                NativeField("Node", "f158", "moGenTextDataList_c"),
                NativeField("Scalar", "f160", "i32"),
                NativeField("Node", "f170", "moDisplayItem_c"),
                NativeField("Embed", "f188", "utParagraphFormat_c"),
            )
        ),
        "moGenTextDataList_c": GateNote(
            (
                NativeField("Node", "f10", "suObArray"),
                NativeField("Scalar", "f128", "i32"),
                NativeField("Embed", "f18", "moGenTextDataList_c.FUN_4bedb600"),
            )
        ),
        "moGenTextDataList_c.FUN_4bedb600": GateNote(
            MakeScalarRows("f64", "f00 f08 f10 f18")
        ),
        "utParagraphFormat_c": GateNote(KNoteParagraphFields),
    }
)
