from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Presentation.RootOrder import (
    ReadRootOrder,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.MakeShellBrep import (
    MakeShellBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellCache import (
    ReadShellCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.SummShellBrep import (
    SummShellBrep,
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
    ReadFreshStock,
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
    _ = ReadRootOrder(Prefix, Features)
    if NativeNodeId(ShellNode) in Features:
        raise ValueError("SOLIDWORKS shell repeats a preceding feature identity")
    return Features


# either body state requires the same real removed cap and independent thickness
def ReadOpenShell(Archive: SldprtArchive, ModelValue: NativeModel) -> ShellPartRead:
    Linked = ReadNativeLink(
        Archive, ModelValue.active_configuration_id, ReadShells=True
    )
    Roots = Linked.ResolvedValue.RootsValue
    StockNode = RequireNative(Roots[-2], "moExtrusion_c")
    ShellNode = RequireNative(Roots[-1], "moShell_c")
    IsSaved = KPartitionStream in Archive.streams
    FreshRoots: tuple[ArchiveNode, ...] = ()
    if IsSaved:
        StockValue = ReadShellStock(
            Linked, StockNode, ShellRootIndex(Linked, ShellNode)
        )
    elif IsCacheAbsent(Archive):
        StockValue, FreshRoots = ReadFreshStock(
            Linked, ModelValue, StockNode, ShellNode
        )
    else:
        raise ValueError("fresh shell has an unqualified physical stream")
    AtomValue = ReadShellAtom(Linked, StockNode, ShellNode, IsSaved=IsSaved)
    Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
    FaceValue = ReadShellPick(
        Linked, ShellNode, StockValue, AtomValue, Header, IsSaved=IsSaved
    )
    Driver = ReadShellDim(Linked, ShellNode)
    Thickness = Driver.DepthValue.value_mm
    if Thickness is None or Driver.Dimension.FieldsValue.get(
        "f50"
    ) == StockValue.OwnerValue.RequireDepth().Dimension.FieldsValue.get("f50"):
        raise ValueError("SOLIDWORKS shell lacks an independent thickness driver")
    Footprint = ShellFootprint(StockValue.BoundsValue, Thickness)
    if IsSaved:
        CheckShellMgr(Linked, StockNode, ShellNode, AtomValue)
        MarksValue = ReadShellMarks(Linked, StockNode, ShellNode)
        Cache = ReadShellCache(
            Archive,
            AtomValue,
            StockValue,
            NativeNodeId(ShellNode),
            MarksValue,
            Header,
            Footprint,
        )
    else:
        Cache = SummShellBrep(MakeShellBrep(Footprint), Footprint)
    return ShellPartRead(
        Linked, StockValue, ShellNode, FaceValue, Driver, AtomValue, Cache, FreshRoots
    )
