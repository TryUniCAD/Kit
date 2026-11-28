from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellCache import (
    ShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)


# one linked saved shell carries the neutral parameters and solved body together
@DataClass(frozen=True, slots=True)
class ShellPartRead:
    LinkValue: NativeLink
    StockValue: ShellStock
    ShellNode: ArchiveNode
    FaceValue: ArchiveNode
    DriverValue: DepthOwner
    AtomValue: ArchiveNode
    CacheValue: ShellCache
