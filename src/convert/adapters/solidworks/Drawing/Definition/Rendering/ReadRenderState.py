from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewNode import (
    NeedViewNode,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadOccColours import (
    ReadOccColours,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadSketchCache import (
    ReadSketchCache,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.RenderState import (
    RenderState,
)


# understood native view state stays separate from unresolved portable colour associations
def ReadRenderState(ViewValue: ArchiveNode, VersionValue: int) -> RenderState:
    if VersionValue != 19000:
        raise BodyUnsupported("drawing view state requires archive version 19000")
    _ = NeedViewNode(ViewValue, "moAbsoluteView")
    Presence, CacheCount = ReadSketchCache(ViewValue.FieldsValue)
    return RenderState(
        ViewValue, Presence, CacheCount, ReadOccColours(ViewValue.FieldsValue)
    )
