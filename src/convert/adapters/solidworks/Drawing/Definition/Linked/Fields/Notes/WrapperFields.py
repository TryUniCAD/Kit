from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KAnchorFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# the selected drawing curve has the native component reference branch while the existing anchor only declaration remains unchanged
KNoteEdgeWrapper = (
    NativeField("Node", "f58", "moCompRef_c"),
    NativeField(
        "Branch",
        "",
        ModeValue="Expression",
        ExpressionValue=(
            "compare",
            ("Eq",),
            ("class_of", ("lookup", ("scope",), ("literal", "f58"))),
            ("literal", "moCompEdge_c"),
        ),
        OtherValue=(
            NativeField(
                "Fail", "note curve wrapper requires its actual component edge"
            ),
        ),
    ),
    *KAnchorFields["moRefWrapper_c"][2:],
)

# note only base aliases reuse the same proved current wrapper tail and curve doubles without widening part anchor admission
KNoteWrapperFields = MappingProxyType(
    {
        "moRefWrapper_c.NoteEdge": GateNote(KNoteEdgeWrapper),
        "moCurveRef_w.NoteEdge": GateNote(
            (
                NativeField("Base", "moRefWrapper_c.NoteEdge"),
                NativeField("Scalar", "fb0", "f64"),
                NativeField("Scalar", "fb8", "f64"),
            )
        ),
    }
)
