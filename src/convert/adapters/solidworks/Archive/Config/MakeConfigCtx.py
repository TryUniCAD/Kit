from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartLayouts import (
    KPartLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartSchemas import (
    KPartSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartVirtuals import (
    KPartVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# one ordinary part graph uses the original model header identities and explicit part owners
def MakeConfigCtx(
    VersionValue: int, HeaderValue: ArchiveNode, UsageValue: BodyUsage | None
) -> BodyContext:
    Usage = NewBodyUsage(VersionValue, UsageValue)
    return BodyContext(
        VersionValue,
        KPartLayouts,
        KPartVirtuals,
        KPartSchemas,
        Usage,
        DirectNodes=HeaderRefNodes(HeaderValue, VersionValue),
    )
