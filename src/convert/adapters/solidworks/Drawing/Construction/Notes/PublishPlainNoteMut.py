from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteRows import (
    ReadNoteRows,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# publishing one note binds its actual display data text and folder and consumes the distinct display counter
def PublishNoteMut(
    ModelValue: ArchiveNode,
    FolderValue: ArchiveNode,
    DisplayValue: ArchiveNode,
    DataValue: ArchiveNode,
    TextValue: ArchiveNode,
    LanguageId: int,
) -> None:
    RowsValue = ReadNoteRows(NeedConceptMap(FolderValue.FieldsValue["f358"]))
    NextValue = FieldInt(ModelValue.FieldsValue, "fd44")
    if (
        LanguageId != 1033
        or RowsValue
        or not 10 <= NextValue < (1 << 31) - 1
        or DisplayValue.FieldsValue["f58"] != 0
        or DataValue.FieldsValue["f18"] is not None
    ):
        raise ValueError(
            "first note publication requires fresh English sheet ownership"
        )
    DataValue.FieldsValue["f18"] = ArchiveNode(
        RuntimeClass("moNodeName_c", 1), {"f08": "DetailItem" + str(len(RowsValue) + 1)}
    )
    ModelValue.FieldsValue["fd44"] = NextValue + 1
    DisplayValue.FieldsValue.update(f30=FolderValue, f58=NextValue)
    DataValue.FieldsValue["f48"] = FolderValue
    TextValue.FieldsValue["f170"] = DisplayValue
    FolderValue.FieldsValue["f358"] = {"n": 1, "items": ({"o": DisplayValue},)}
