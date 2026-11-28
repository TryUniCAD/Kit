from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteData import (
    MakeNoteData,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteDisplay import (
    MakeNoteDisplay,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteReference import (
    MakeNoteRef,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteText import (
    MakeNoteText,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.PublishPlainNoteMut import (
    PublishNoteMut,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.SetNotePointMut import (
    SetNotePointMut,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)
from interchange.document.Models.Drawing.DrawingNote import DrawingNote


# the complete generated note must attach its local objects to the actual sheet before definition serialization
def PutPlainNoteMut(
    GraphValue: DrawRootGraph,
    NoteValue: DrawingNote,
    VersionValue: int,
    LanguageId: int,
) -> None:
    ModelValue = GraphValue.ModelValue
    DetailsValue = NeedConceptMap(ModelValue.FieldsValue["fae0"])
    if VersionValue != 19000 or FieldInt(DetailsValue, "f20") & 0x10000:
        raise ValueError(
            "plain note construction requires the ordinary current text parser"
        )
    AnnotationValue = NeedConceptMap(DetailsValue["f1f18"])
    StyleValue = NeedConceptMap(AnnotationValue["f418"])
    TextValue = MakeNoteText(NoteValue, StyleValue)
    DataValue = MakeNoteData(TextValue)
    DisplayValue = MakeNoteDisplay(
        MakeNoteRef(DataValue, VersionValue), StyleValue, VersionValue
    )
    FolderValue = NeedConceptNode(
        GraphValue.SheetValue.SheetValue.FieldsValue["f390"], "moDetailFolder_c"
    )
    SetNotePointMut(DisplayValue, DataValue, NoteValue.PositionValue)
    PublishNoteMut(
        ModelValue, FolderValue, DisplayValue, DataValue, TextValue, LanguageId
    )
