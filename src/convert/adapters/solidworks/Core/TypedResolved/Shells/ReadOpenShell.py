from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRoots import (
    ReadChmfPrefix,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellCache import (
    ReadShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.CheckShellMgr import (
    CheckShellMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.ReadShellAtom import (
    ReadShellAtom,
    ReadShellMarks,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.ReadShellDim import (
    ReadShellDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Owners.ReadShellPick import (
    ReadShellPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.ShellPartRead import (
    ShellPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ReadShellStock import (
    ReadShellStock,
)


# only one later modifier may follow the complete ordinary rectangular stock root tree
def ShellRootIndex(
    LinkValue: NativeLink, ShellNode: ArchiveNode
) -> dict[int, ArchiveNode]:
    Resolved = LinkValue.ResolvedValue
    if (
        Resolved.ExtraFields != {"n": 0, "fcd8": []}
        or Resolved.RootsValue[-1] is not ShellNode
    ):
        raise ValueError(
            "SOLIDWORKS shell requires its exact stock and modifier sequence"
        )
    Prefix = ReplaceValue(
        LinkValue,
        ResolvedValue=ReplaceValue(Resolved, RootsValue=Resolved.RootsValue[:-1]),
    )
    Features = IndexFeatures(Prefix)
    _ = ReadChmfPrefix(Prefix, Features)
    if NativeNodeId(ShellNode) in Features:
        raise ValueError("SOLIDWORKS shell repeats a preceding feature identity")
    return Features


# the bounded saved shell requires one actual cap and the matching active native solid
def ReadOpenShell(Archive: SldprtArchive, ConfigId: int | None) -> ShellPartRead:
    Linked = ReadNativeLink(Archive, ConfigId, ReadShells=True)
    Roots = Linked.ResolvedValue.RootsValue
    StockNode = RequireNative(Roots[-2], "moExtrusion_c")
    ShellNode = RequireNative(Roots[-1], "moShell_c")
    StockValue = ReadShellStock(Linked, StockNode, ShellRootIndex(Linked, ShellNode))
    AtomValue = ReadShellAtom(Linked, StockNode, ShellNode)
    CheckShellMgr(Linked, StockNode, ShellNode, AtomValue)
    MarksValue = ReadShellMarks(Linked, StockNode, ShellNode)
    Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
    FaceValue = ReadShellPick(Linked, ShellNode, StockValue, AtomValue, Header)
    Driver = ReadShellDim(Linked, ShellNode)
    Thickness = Driver.DepthValue.value_mm
    if Thickness is None or Driver.Dimension.FieldsValue.get(
        "f50"
    ) == StockValue.OwnerValue.DepthValue.Dimension.FieldsValue.get("f50"):
        raise ValueError("SOLIDWORKS shell lacks an independent thickness driver")
    Cache = ReadShellCache(
        Archive,
        AtomValue,
        StockValue,
        NativeNodeId(ShellNode),
        MarksValue,
        Header,
        ShellFootprint(StockValue.BoundsValue, Thickness),
    )
    return ShellPartRead(
        Linked, StockValue, ShellNode, FaceValue, Driver, AtomValue, Cache
    )
