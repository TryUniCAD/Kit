from collections.abc import Callable

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigLayouts import (
    KConfigLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigSchemas import (
    KConfigSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigVirtuals import (
    KConfigVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Config.UsePartRelationsMut import (
    BindPartRelsMut,
)
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# external header aliases must be selected before reading without seeding the configuration map
def MakeConfigCtx(
    VersionValue: int,
    HeaderValue: ArchiveNode,
    UsageValue: BodyUsage | None,
    ReadItems: Callable[[ArchiveNode], tuple[ArchiveNode, ...]],
    *,
    PartRelations: bool = False,
) -> BodyContext:
    UsageValue = NewBodyUsage(VersionValue, UsageValue)
    DirectNodes = HeaderRefNodes(HeaderValue, VersionValue, ReadItems)
    ContextValue = BodyContext(
        VersionValue,
        KConfigLayouts,
        KConfigVirtuals,
        KConfigSchemas,
        UsageValue,
        DirectNodes=DirectNodes,
    )
    if PartRelations:
        BindPartRelsMut(ContextValue)
    return ContextValue
