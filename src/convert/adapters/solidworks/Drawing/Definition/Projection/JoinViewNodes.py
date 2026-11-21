from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.CheckViewRef import (
    CheckViewRef,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewOwners import (
    JoinViewOwners,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadOwnedNodes import (
    ReadOwnedNodes,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet

# a regular sheet owns stocked model support objects alongside its native views
KSheetClassNames = frozenset(
    {"moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c", "moAbsoluteView"}
)


# model views are joined in resolved concept order and validated against their directory
def JoinViewNodes(
    NodesOwner: ArchiveNode, HeaderNode: ArchiveNode, Layout: DrawingData
) -> DrawingSheet:
    Sheet = Layout.Sheets[0]
    Nodes = ReadOwnedNodes(NodesOwner)
    if any(
        ItemValue.ClassValue.NameValue not in KSheetClassNames for ItemValue in Nodes
    ):
        raise ValueError("unsupported SOLIDWORKS drawing sheet contents")
    Views = tuple(
        ItemValue
        for ItemValue in Nodes
        if ItemValue.ClassValue.NameValue == "moAbsoluteView"
    )
    Directory = HeaderNode.FieldsValue.get("directory")
    if (
        len(Views) != len(Sheet.Views)
        or len(Views) > 1
        or len(Layout.ModelRefs) != len(Views)
        or (Directory is None) != (not Views)
    ):
        raise ValueError("drawing Definition and native sheet view indexes disagree")
    if not Views:
        return Sheet
    Linked = NeedConceptNode(Directory, "moExtObjectList_c")
    ViewValue = Sheet.Views[0]
    CheckViewRef(Views[0], Linked, Layout.ModelRefs[0], ViewValue.ConfigurationName)
    return ReplaceValue(Sheet, Views=(JoinViewOwners(Views[0], ViewValue),))
