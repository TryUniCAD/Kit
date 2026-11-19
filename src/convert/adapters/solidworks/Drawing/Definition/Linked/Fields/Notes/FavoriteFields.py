from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# the current favorite handle contributes two signed words and one unsigned word without serializing its runtime address
KNoteFavoriteFields = MappingProxyType(
    {
        "moFavoriteHandle_c": GateNote(
            (
                NativeField("Scalar", "f08", "i32"),
                NativeField("Scalar", "f0c", "i32"),
                NativeField("Scalar", "f10", "u32"),
            )
        ),
    }
)
