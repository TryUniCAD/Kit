from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# a null component makes both native external owner predicates false without resolving a runtime file table
KLocalDetailFields = (
    NativeField("Base", "moCompRef_c"),
    NativeField(
        "Branch",
        "",
        BodyValue=(
            NativeField("Node", "fe8", "moDetailItem_c"),
            NativeField("Node", "ff8", "moDetailItem_c"),
            NativeField("Scalar", "f100", "i32"),
        ),
        OtherValue=(
            NativeField(
                "Fail",
                "nonnull component detail item requires actual filed-owner branch",
            ),
        ),
        ModeValue="Expression",
        ExpressionValue=(
            "compare",
            ("Eq",),
            ("lookup", ("scope",), ("literal", "f58")),
            ("literal", None),
        ),
    ),
)

# current detail and note data keep the actual node attachment array and separate typed text object
KNoteDetailFields = MappingProxyType(
    {
        "moCompDetailItem_c": GateNote(KLocalDetailFields),
        "moCompNote_c": GateNote((NativeField("Base", "moCompDetailItem_c"),)),
        "moDetailItem_c": GateNote(
            (
                NativeField("Base", "moNode_c"),
                NativeField("Scalar", "f50", "u16"),
                NativeField("Node", "f48"),
                NativeField("Embed", "f58", "rf.suObArray"),
                NativeField(
                    "Array",
                    "f68",
                    "i32",
                    BodyValue=(NativeField("Scalar", "v", "i32"),),
                    CountValue="n70",
                    ModeValue="Positive",
                ),
                NativeField("Scalar", "f80", "i32"),
                NativeField("Node", "f88", "moAttachPoint_c"),
            )
        ),
        "moNoteData_c": GateNote(
            (
                NativeField("Base", "moDetailItem_c"),
                NativeField("Node", "f98", "moDimText_c"),
            )
        ),
    }
)
