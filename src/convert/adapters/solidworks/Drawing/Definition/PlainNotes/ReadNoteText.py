from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteRows import (
    ReadNoteRows,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)
from interchange.document.Models.Drawing.ValidText import HasDrawingText


# a plain note string must agree with the actual ordered text objects without property or control nodes
def ReadNoteText(NoteText: ArchiveNode) -> str:
    FieldsValue = NoteText.FieldsValue
    BaseValue = FieldsValue.get("f08")
    ListValue = NeedConceptNode(FieldsValue.get("f158"), "moGenTextDataList_c")
    ArrayValue = NeedConceptNode(ListValue.FieldsValue.get("f10"), "suObArray")
    RowValues = ReadNoteRows(ArrayValue.FieldsValue)
    if (
        not isinstance(BaseValue, str)
        or not HasDrawingText(BaseValue)
        or FieldsValue.get("f18") is not None
        or len(RowValues) < 2
        or RowValues[0].ClassValue.NameValue != "moTextDataLineHead_c"
    ):
        raise BodyUnsupported("unsupported plain drawing note text state")
    Payload = bytearray()
    for RowValue in RowValues[1:]:
        CodeUnit = RowValue.FieldsValue.get("f40")
        if (
            RowValue.ClassValue.NameValue != "moTextDataChar_c"
            or type(CodeUnit) is not int
            or not 0 <= CodeUnit <= 65535
        ):
            raise BodyUnsupported("plain drawing note needs ordinary text characters")
        Payload.extend(CodeUnit.to_bytes(2, "little"))
    if Payload.decode("utf-16-le") != BaseValue or any(
        Character in BaseValue for Character in ("\0", "\r", "\n")
    ):
        raise BodyUnsupported("drawing note text representations differ")
    return BaseValue
