from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.ViewProjection import (
    ViewProjection,
)
from convert.adapters.solidworks.Drawing.Construction.References.MakeDrawRefsMut import (
    MakeDrawRefsMut,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ProfileTime import (
    MakeProfileTime,
)
from convert.adapters.solidworks.Drawing.Construction.Supports.MakeSupportsMut import (
    MakeSupportsMut,
)
from convert.adapters.solidworks.Drawing.Construction.Supports.ViewNames import (
    ViewNames,
)
from convert.adapters.solidworks.Drawing.Construction.View.MakeViewState import (
    MakeViewState,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
    NeedDrawNumber,
)
from interchange.document.Models.Drawing.DrawingView import DrawingView


# a real linked view extends the existing active sheet without replacing any original model support or child identity
def MakeLinkedView(
    GraphValue: DrawRootGraph,
    ChildValue: PartCandidate,
    BuildValue: DrawBuild,
    IntentValue: DrawingView,
    Projection: ViewProjection,
    NamesValue: ViewNames,
) -> ArchiveNode:
    OwnerValue = GraphValue.ModelValue
    SheetValue = GraphValue.SheetValue.SheetValue
    Children = ReadBlankKids(SheetValue)
    if (
        tuple(NodeValue.ClassValue.NameValue for NodeValue in Children)
        != ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c")
        or OwnerValue.FieldsValue["n1578"]
        or OwnerValue.FieldsValue["n1740"]
    ):
        raise ValueError(
            "linked drawing construction requires the actual fresh unformatted sheet"
        )
    CheckDrawText(IntentValue.EntityName, True)
    ViewValue = ArchiveNode(RuntimeClass("moAbsoluteView", 1), {})
    InitFeatureMut(
        ViewValue, IntentValue.EntityName, SheetValue, BuildValue.TargetValue
    )
    ViewValue.FieldsValue.update(
        MakeViewState(OwnerValue, ChildValue, Projection.AxisValues[2])
    )
    ViewValue.FieldsValue.update(
        {
            "f35c": 0,
            **Projection.FieldsValue,
            **MakeProfileTime(BuildValue.CreatedAt),
            "f0c": 0,
        }
    )
    BoundsValue = {
        NameValue: NeedDrawNumber(Value)
        for NameValue, Value in NeedConceptMap(Projection.FieldsValue["f600"]).items()
    }
    References = MakeDrawRefsMut(GraphValue, ChildValue, BoundsValue, BuildValue)
    ViewValue.FieldsValue["f5d8"] = References.InternalValue
    MakeSupportsMut(ViewValue, GraphValue, BuildValue, Projection, NamesValue)
    AllChildren = (*Children, ViewValue)
    SheetValue.FieldsValue["f60"] = {
        "list": {
            "n": len(AllChildren),
            "items": tuple({"o": NodeValue} for NodeValue in AllChildren),
        },
        "tail": 0,
    }
    HeaderValue = NeedConceptNode(OwnerValue.FieldsValue["fa8"], "moHeader_c")
    HeaderValue.FieldsValue.update(
        {
            "f08": GraphValue.Allocator.NextValue,
            "bbox": tuple(Projection.HeaderBounds[f"b{Index}"] for Index in range(10)),
        }
    )
    return ViewValue
