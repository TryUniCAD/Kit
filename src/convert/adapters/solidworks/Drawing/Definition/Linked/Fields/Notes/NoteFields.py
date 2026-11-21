from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteHead import (
    KNoteHead,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteTail import (
    KNoteTail,
)

# independently proved note framing reuses the shared display item fields and archive object maps
KNoteFields = MappingProxyType(
    {
        "moDisplayNote_c": GateNote((*KNoteHead, *KNoteTail)),
        "suHyperlink_c": GateNote((NativeField("Text", "f08"),)),
        "su_CMapStringToInt": GateNote(
            (
                NativeField(
                    "Array",
                    "items",
                    "Framework",
                    BodyValue=(
                        NativeField("Text", "k"),
                        NativeField("Scalar", "v", "i32"),
                    ),
                    CountValue="n",
                ),
            )
        ),
    }
)
