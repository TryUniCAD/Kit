from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadConceptName import (
    ReadConceptName,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadOwnedNodes import (
    ReadOwnedNodes,
)
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet

# the selected drawing profile admits the ordinary root stock folders and one sheet
KDrawingFolderNames = frozenset(
    {
        "moCommentsFolder_c",
        "moBlockFolder_c",
        "moDocsFolder_c",
        "moDetailCabinet_c",
        "moInkMarkupFolder_c",
        "moMarkupCommentFolder_c",
    }
)


# the native resolved concept must agree with the independent sheet identity
def MatchSheetNode(RootValue: ArchiveNode, Sheet: DrawingSheet) -> ArchiveNode:
    Nodes = ReadOwnedNodes(RootValue)
    Owners = tuple(
        ItemValue
        for ItemValue in Nodes
        if ItemValue.ClassValue.NameValue == "moDrSheet"
    )
    Classes = frozenset(ItemValue.ClassValue.NameValue for ItemValue in Nodes)
    if (
        len(Owners) != 1
        or len(Nodes) != len(KDrawingFolderNames) + 1
        or Classes - {"moDrSheet"} != KDrawingFolderNames
    ):
        raise ValueError("unsupported SOLIDWORKS drawing sheet ownership")
    Native = Owners[0]
    Fields = Native.FieldsValue
    if (
        ReadConceptName(Native) != Sheet.EntityName
        or Fields.get("f3c0") != 13
        or (Fields.get("f3f8"), Fields.get("f400")) != Sheet.ScaleRatio
        or not IsClose(
            NeedDrawNumber(Fields.get("f3f0")), Sheet.SheetWidth, abs_tol=1e-12
        )
        or not IsClose(
            NeedDrawNumber(Fields.get("f3e8")), Sheet.SheetHeight, abs_tol=1e-12
        )
    ):
        raise ValueError("drawing Definition and native sheet indexes disagree")
    return Native
