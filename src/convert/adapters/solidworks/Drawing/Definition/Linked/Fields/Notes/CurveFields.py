from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# the exact general curve wrapper delegates its curve base and preserves presence governed body data and actual reference tags
KNoteCurveFields = MappingProxyType(
    {
        "moGeneralCurveRef_w": GateNote(
            (
                NativeField("Base", "moCurveRef_w.NoteEdge"),
                NativeField("Scalar", "has_fc8", "u8"),
                NativeField(
                    "Branch",
                    "has_fc8",
                    BodyValue=(NativeField("Embed", "fc8", "mo_loadBodyFromArchive"),),
                    ModeValue="Nonzero",
                ),
                NativeField("Scalar", "fd0", "u32"),
                NativeField("Scalar", "fd4", "i32"),
                NativeField("Node", "fe0", "moContourChooser_c"),
                NativeField("Node", "fd8", "moCompSketchEntHandle_c"),
                NativeField("Node", "fe8", "moContourChooser_c"),
            )
        ),
    }
)
