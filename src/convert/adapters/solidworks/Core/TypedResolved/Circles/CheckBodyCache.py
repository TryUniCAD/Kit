from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.Cache.CheckCacheBox import (
    CheckCacheBox,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.Cache.CheckCacheFile import (
    CheckCacheFile,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.Cache.ReadCacheRows import (
    ReadCacheRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.Cache.ReadChooser import (
    ReadChooser,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# live radial edits remain portable when chooser records only snapshot the same prior local body
def CheckBodyCache(
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    CircleValue: LocalCircle,
    InactiveDepth: float,
    Configuration: str,
) -> None:
    (First,) = ReadCacheRows(BossValue, "f4a8", 1)
    _ = ReadCacheRows(BossValue, "f4b0", 0)
    (LastRow,) = ReadCacheRows(BossValue, "f4c0", 1)
    FirstRefs, FirstBox = ReadChooser(First, BossValue, CircleValue.ArcMark)
    LastRefs, LastBox = ReadChooser(LastRow, BossValue, CircleValue.ArcMark)
    if FirstRefs != LastRefs or FirstRefs[0][-1] is not FirstRefs[1][-1]:
        raise ValueError(
            "SOLIDWORKS attached circle chooser has conflicting historical face identities"
        )
    CheckCacheFile(LinkValue, FirstRefs[0][-1], Configuration)
    CheckCacheBox(FirstBox, CircleValue, InactiveDepth)
    CheckCacheBox(LastBox, CircleValue, InactiveDepth)
