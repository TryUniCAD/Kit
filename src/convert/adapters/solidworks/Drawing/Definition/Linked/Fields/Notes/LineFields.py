from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# line heads retain the actual generic text words two float metrics narrowed wire boolean paragraph and nested text list
KNoteLineFields = MappingProxyType(
    {
        "moGenTextData_c": GateNote(MakeScalarRows("i32", "f08 f0c")),
        "moTextDataLineHead_c": GateNote(
            (
                NativeField("Base", "moGenTextData_c"),
                NativeField("Embed", "f14", "moTextDataLineHead_c.FUN_4bed8ec0"),
                NativeField("Scalar", "f10", "u16"),
                NativeField("Embed", "f30", "utParagraphFormat_c"),
                NativeField("Embed", "f38", "moTextDataLineHead_c.FUN_4bed8ec0"),
                NativeField("Node", "f48", "moGenTextDataList_c"),
                NativeField("Scalar", "f50", "i32"),
                NativeField("Scalar", "f58", "f64"),
                NativeField("Scalar", "f64", "i32"),
            )
        ),
        "moTextDataLineHead_c.FUN_4bed8ec0": GateNote(
            MakeScalarRows("f32", "f00 f04 f08")
        ),
    }
)
