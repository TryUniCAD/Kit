from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.DrawSheetIndex import (
    DrawSheetIndex,
)


# drawing indexes must reflect the constructed sheet fields instead of a parallel template or captured metadata table
def ReadSheetIndex(SheetValue: ArchiveNode) -> DrawSheetIndex:
    RequireRootNode(SheetValue, "moDrSheet")
    FieldsValue = SheetValue.FieldsValue
    NameValue = NeedConceptNode(FieldsValue["f18"], "moNodeName_c").FieldsValue["f08"]
    PropertyView = FieldsValue["f3d0"]
    CheckDrawText(NameValue, True)
    CheckDrawText(PropertyView, True)
    Identifier = FieldsValue["f08"]
    if (
        type(Identifier) is not int
        or not 1 <= Identifier <= 2147483647
        or (FieldsValue["f39c"], FieldsValue["f3c0"], FieldsValue["f3b8"])
        != (0, 13, "*.drt")
        or not isinstance(NameValue, str)
        or not isinstance(PropertyView, str)
    ):
        raise ValueError(
            "drawing metadata requires the ordinary constructed unformatted sheet"
        )
    return DrawSheetIndex(
        Identifier,
        NameValue,
        PropertyView,
        NeedDrawNumber(FieldsValue["f3f0"]),
        NeedDrawNumber(FieldsValue["f3e8"]),
        NeedDrawNumber(FieldsValue["f3f8"]),
        NeedDrawNumber(FieldsValue["f400"]),
    )
