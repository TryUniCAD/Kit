from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# parametric attachments carry their wrapper and point tail after the base attachment
KParametricPointFields = (
    NativeField("Base", "moAttachPoint_c"),
    NativeField("Scalar", "f108", "f64"),
    NativeField("Scalar", "f110", "f64"),
    NativeField("Node", "f118", "moRefWrapper_c"),
    NativeField("Scalar", "f124", "u16"),
    NativeField("Scalar", "f130", "i32"),
    NativeField("Embed", "f138", "mgPoint_c.restore"),
    NativeField("Embed", "f150", "mgPoint_c.restore"),
    NativeField("Embed", "f168", "mgPoint_c.restore"),
    NativeField("Embed", "f180", "mgPoint_c.restore"),
    NativeField("Embed", "f198", "mgPoint_c.restore"),
)

# ordinary drawing attachments use one point and view field order for each native owner
KNoteAttachFields = MappingProxyType(
    {
        "moAttachPointData_c": GateNote(
            (
                NativeField("Embed", "f08", "mgPoint_c.restore"),
                NativeField("Embed", "f20", "mgPoint_c.restore"),
                NativeField("Node", "f38", "moDrView"),
                NativeField("Scalar", "f40", "f64"),
                NativeField("Scalar", "f48", "f64"),
            )
        ),
        "moAttachPoint_c": GateNote(
            (
                NativeField("Embed", "f08", "mgPoint_c.restore"),
                NativeField("Embed", "f28", "mgPoint_c.restore"),
                NativeField("Scalar", "f20", "i32"),
                NativeField("Node", "f50", "moDrView"),
                NativeField("Embed", "f58", "mgPoint_c.restore"),
                NativeField("Embed", "f70", "mgPoint_c.restore"),
                NativeField("Scalar", "f88", "u8"),
            )
        ),
        "moParametricPoint_c": GateNote(KParametricPointFields),
    }
)
