from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadLinkedBody import (
    ReadLinkedBody,
)
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteRows import (
    NeedOneNoteRow,
)
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteText import (
    ReadNoteText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.MatchSheetNode import (
    MatchDrawOwners,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.geometry.Models.VectorSpace import SpaceVector


# an inspected note retains the document sheet and inherited text position instead of using the attachment cache
def ReadNoteDrawing(
    DataValue: bytes, VersionValue: int, LayoutValue: DrawingData
) -> DrawingData:
    if (
        len(LayoutValue.Sheets) != 1
        or LayoutValue.ModelRefs
        or LayoutValue.Sheets[0].Views
    ):
        raise BodyUnsupported("plain drawing note requires one unlinked sheet")
    Document, _, _ = ReadLinkedBody(DataValue, VersionValue, "plain note")
    DrawingRoot = NeedConceptNode(Document.FieldsValue.get("model"), "moDrawing_c")
    SheetValue = LayoutValue.Sheets[0]
    NativeSheet = MatchDrawOwners(ReadBlankKids(DrawingRoot), SheetValue)
    if DrawingRoot.FieldsValue.get("f1430") is not NativeSheet:
        raise BodyUnsupported("drawing note refers to a different active sheet")
    TextValue = ReadPlainNote(NativeSheet)
    Point = NeedConceptMap(TextValue.FieldsValue.get("f38"))
    NoteValue = DrawingNote(
        SheetValue.EntityId + "/note/1",
        ReadNoteText(TextValue),
        SpaceVector(
            NeedDrawNumber(Point.get("x")),
            NeedDrawNumber(Point.get("y")),
            NeedDrawNumber(Point.get("z")),
        ),
    )
    return ReplaceValue(
        LayoutValue, Sheets=(ReplaceValue(SheetValue, Notes=(NoteValue,)),)
    )


# only the actual sheet detail folder may supply an unattached plain note
def ReadPlainNote(Sheet: ArchiveNode) -> ArchiveNode:
    Children = ReadBlankKids(Sheet)
    Folder = NeedConceptNode(Sheet.FieldsValue.get("f390"), "moDetailFolder_c")
    if (
        tuple(Child.ClassValue.NameValue for Child in Children)
        != ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c")
        or Children[2] is not Folder
    ):
        raise BodyUnsupported("unqualified drawing note sheet owners")
    Display = NeedOneNoteRow(Folder, "f358", "moDisplayNote_c")
    Component = NeedConceptNode(Display.FieldsValue.get("f48"), "moCompNote_c")
    NoteData = NeedConceptNode(Component.FieldsValue.get("fe8"), "moNoteData_c")
    TextValue = NeedConceptNode(NoteData.FieldsValue.get("f98"), "moGenericText_c")
    Attachment = NeedOneNoteRow(Display, "f298", "moAttachPointData_c")
    _ = NeedOneNoteRow(NoteData, "f58", "moAbsolutePoint_c")
    if (
        Display.FieldsValue.get("f30") is not Folder
        or NoteData.FieldsValue.get("f48") is not Folder
        or TextValue.FieldsValue.get("f170") is not Display
        or Component.FieldsValue.get("f58") is not None
        or Attachment.FieldsValue.get("f38") is not None
        or any(
            Display.FieldsValue.get(Field) is not None
            for Field in ("f5a0", "f590", "f6a0", "f6b8")
        )
    ):
        raise BodyUnsupported("unsupported drawing note owner or attachment")
    return TextValue
