from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# spacing and character owners preserve float metrics narrowed boolean words and the actual unsigned character code unit
KNoteCharacterFields = MappingProxyType(
    {
        "moTextDataControl_c": GateNote((NativeField("Base", "moGenTextData_c"),)),
        "moTextDataSpaceHolder_c": GateNote(
            (
                NativeField("Base", "moGenTextData_c"),
                NativeField("Embed", "f20", "moTextDataLineHead_c.FUN_4bed8ec0"),
                NativeField("Scalar", "f2c", "f32"),
                NativeField("Scalar", "f30", "u16"),
                NativeField("Scalar", "f34", "i32"),
                NativeField("Scalar", "f38", "f32"),
                NativeField("Scalar", "f10", "u16"),
            )
        ),
        "moTextDataChar_c": GateNote(
            (
                NativeField("Base", "moTextDataSpaceHolder_c"),
                NativeField("Scalar", "f40", "u16"),
            )
        ),
    }
)
