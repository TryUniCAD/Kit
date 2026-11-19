from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteGate import (
    GateNote,
)

# the concrete absolute point vtable delegates directly to the already bound attachment serializer with no subclass wire fields
KNoteAbsoluteFields = MappingProxyType(
    {"moAbsolutePoint_c": GateNote((NativeField("Base", "moAttachPoint_c"),))}
)
