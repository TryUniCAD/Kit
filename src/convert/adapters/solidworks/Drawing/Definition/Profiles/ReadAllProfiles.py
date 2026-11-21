from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileSet import (
    ProfileSet,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadProfileSet import (
    ReadProfileSet,
)


# result metadata must retain every actual detail folder without guessing archive indices
def ReadAllProfiles(Document: ArchiveNode, VersionValue: int) -> tuple[ProfileSet, ...]:
    if VersionValue != 19000:
        raise BodyUnsupported("drawing profile display requires archive version 19000")
    _ = NeedProfileNode(Document, "uiDrawingDoc_c")
    return tuple(
        ReadProfileSet(NodeValue, VersionValue)
        for NodeValue in WalkDrawNodes(Document)
        if NodeValue.ClassValue.NameValue == "moDetailFolder_c"
    )
