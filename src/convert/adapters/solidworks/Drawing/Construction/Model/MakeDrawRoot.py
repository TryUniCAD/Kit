from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import (
    InitConceptMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Model.BindSheetIdsMut import (
    BindSheetIdsMut,
)
from convert.adapters.solidworks.Drawing.Construction.Model.CheckDrawBuild import (
    CheckDrawBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.Model.InitDrawMut import (
    InitDrawMut,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawCabinet import (
    MakeDrawCabinet,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawFolder import (
    MakeDrawFolder,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawRefs import (
    MakeDrawRefs,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawTail import (
    MakeDrawTail,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeSheetBuild import (
    MakeSheetBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeBlankSheet import (
    MakeBlankSheet,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# a fresh blank drawing must construct its entire owned model and sheet graph from neutral inputs before serialization
def MakeDrawRoot(
    BuildValue: DrawBuild, *, UseDrawingAnsi: bool = False
) -> DrawRootGraph:
    CheckDrawBuild(BuildValue)
    RefsValue = MakeDrawRefs(BuildValue, UseDrawingAnsi=UseDrawingAnsi)
    Allocator = PersistentIds()
    ModelValue = ArchiveNode(RuntimeClass("moDrawing_c", 1), {})
    InitConceptMut(ModelValue, BuildValue.NameValue, Allocator)
    InitDrawMut(ModelValue, RefsValue)
    ClearSystemMut(ModelValue)
    NamesValue, TargetValue = BuildValue.FolderValue, BuildValue.TargetValue
    Cabinet = MakeDrawCabinet(
        NamesValue.CabinetName, ModelValue, TargetValue, Allocator
    )
    Binder = MakeDrawFolder(
        "moDocsFolder_c",
        NamesValue.BinderName,
        ModelValue,
        TargetValue,
        BuildValue.CreatedAt,
        Allocator,
    )
    Comments = MakeDrawFolder(
        "moCommentsFolder_c",
        NamesValue.CommentsName,
        ModelValue,
        TargetValue,
        BuildValue.CreatedAt,
        Allocator,
    )
    SheetValue = MakeBlankSheet(
        MakeSheetBuild(BuildValue, Allocator.NextValue),
        ModelValue,
        NeedConceptNode(ModelValue.FieldsValue["f990"], "moUnitComponent_c"),
    )
    BindSheetIdsMut(SheetValue, Allocator)
    InkValue = MakeDrawFolder(
        "moInkMarkupFolder_c",
        NamesValue.InkName,
        ModelValue,
        TargetValue,
        BuildValue.CreatedAt,
        Allocator,
    )
    Blocks = MakeDrawFolder(
        "moBlockFolder_c",
        NamesValue.BlocksName,
        ModelValue,
        TargetValue,
        BuildValue.CreatedAt,
        None,
    )
    Reviews = MakeDrawFolder(
        "moMarkupCommentFolder_c",
        NamesValue.ReviewName,
        ModelValue,
        TargetValue,
        BuildValue.CreatedAt,
        None,
    )
    Children = (
        Comments,
        Blocks,
        Binder,
        Cabinet,
        InkValue,
        Reviews,
        SheetValue.SheetValue,
    )
    ModelValue.FieldsValue["f60"] = {
        "list": {
            "n": len(Children),
            "items": tuple({"o": NodeValue} for NodeValue in Children),
        },
        "tail": 0,
    }
    ModelValue.FieldsValue.update(
        MakeDrawTail(ModelValue, SheetValue.SheetValue, BuildValue)
    )
    return DrawRootGraph(ModelValue, SheetValue, Allocator)
