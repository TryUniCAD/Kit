from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewNodes import (
    JoinViewNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.MatchSheetNode import (
    MatchSheetNode,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData


# native model objects must corroborate the public layout before projection
def JoinConcept(RootValue: ArchiveNode, Layout: DrawingData) -> DrawingData:
    if len(Layout.Sheets) != 1:
        raise ValueError("drawing inspection supports one ordinary sheet")
    Inline = NeedConceptNode(RootValue.FieldsValue.get("fa8"), "moHeader_c")
    Header = Inline.FieldsValue.get("header")
    if not isinstance(Header, NativeHeader) or Header.SelfFile.KindValue != 4:
        raise ValueError("drawing concept has an invalid inline header")
    Native = MatchSheetNode(RootValue, Layout.Sheets[0])
    return ReplaceValue(Layout, Sheets=(JoinViewNodes(Native, Inline, Layout),))
