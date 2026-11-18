from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewNode import (
    NeedViewNode,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadRenderState import (
    ReadRenderState,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.RenderState import (
    RenderState,
)


# result metadata must follow the actual active view rather than a guessed identifier
def ReadGraphRender(Document: ArchiveNode, VersionValue: int) -> RenderState:
    _ = NeedViewNode(Document, "uiDrawingDoc_c")
    ModelValue = NeedViewNode(Document.FieldsValue.get("model"), "moDrawing_c")
    SheetValue = NeedViewNode(ModelValue.FieldsValue.get("f1430"), "moDrSheet")
    ViewsValue = tuple(
        NodeValue
        for NodeValue in ReadBlankKids(SheetValue)
        if NodeValue.ClassValue == RuntimeClass("moAbsoluteView", 1)
    )
    if len(ViewsValue) != 1:
        raise BodyUnsupported("drawing view state requires one actual active view")
    return ReadRenderState(ViewsValue[0], VersionValue)
