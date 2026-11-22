from collections.abc import Callable, Mapping
from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.CheckEllipUse import CheckEllipUse
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ReadMbsMut import ReadMbsMut
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.Sweeps.ReadSwSchema import (
    ReadSwSchema,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSavedSwMut import (
    UseSavedSwMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.WriteSwSchema import (
    CheckSweepUse,
)
from convert.adapters.solidworks.Archive.Resolved.UseChmfCtxMut import UseChmfCtxMut
from convert.adapters.solidworks.Archive.Resolved.UseEllipCtxMut import UseEllipCtxMut
from convert.adapters.solidworks.Archive.Resolved.UseFilletCtxMut import UseFilletCtxMut
from convert.adapters.solidworks.Archive.Resolved.UseShellCtxMut import UseShellCtxMut


# special read scopes use mutually exclusive feature owners without changing ordinary dispatch
def UseReadCtxMut(
    ContextValue: BodyContext,
    ReadFillets: bool,
    ReadChamfers: bool,
    ReadEllipses: bool,
    ReadShells: bool,
) -> None:
    if ReadShells:
        if ReadFillets or ReadChamfers or ReadEllipses:
            raise BodyUnsupported(
                "SOLIDWORKS shell requires its exclusive archive scope"
            )
        UseShellCtxMut(ContextValue)
    if ReadFillets and ReadChamfers:
        raise BodyUnsupported("SOLIDWORKS resolved edge finish scopes are exclusive")
    if ReadFillets:
        UseFilletCtxMut(ContextValue)
    if ReadChamfers:
        UseChmfCtxMut(ContextValue)
    if ReadEllipses:
        if ReadFillets or ReadChamfers:
            raise BodyUnsupported(
                "SOLIDWORKS ellipse scope excludes edge finish layouts"
            )
        UseEllipCtxMut(ContextValue)


# resolved features extend the exact configuration snapshot after verifying the stored inherited base
def ReadResolvedMut(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    *,
    UsageValue: BodyUsage | None = None,
    NodeMaker: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None,
    ReadFillets: bool = False,
    ReadChamfers: bool = False,
    ReadEllipses: bool = False,
    ReadShells: bool = False,
    SavedSweep: bool = False,
) -> ResolvedGraph:
    ContextValue = MakeResolvedCtx(VersionValue, SeedValue, LinkContext, UsageValue)
    if SavedSweep:
        if ReadFillets or ReadChamfers or ReadEllipses or ReadShells:
            raise BodyUnsupported(
                "SOLIDWORKS saved sweep requires its own archive scope"
            )
        UseSavedSwMut(ContextValue)
        BodyReader = PartialValue(ReadBodyMut, ContextValue, SchemaReader=ReadSwSchema)
    else:
        UseReadCtxMut(ContextValue, ReadFillets, ReadChamfers, ReadEllipses, ReadShells)
        BodyReader = PartialValue(ReadBodyMut, ContextValue)
    Cursor = BinaryReader(BufferValue)
    BaseValue = Cursor.ReadUnsigned(4)
    if BaseValue != SeedValue.CounterValue:
        raise BodyUnsupported(
            "resolved archive base differs from its actual configuration snapshot"
        )
    CountValue, Cursor.OffsetValue = ReadCount(Cursor.BytesValue, Cursor.OffsetValue)
    CountValue = NormalizeCount(CountValue, "")
    ReaderValue = GraphReader(
        Cursor,
        ArchiveMaps(BaseValue, SeedValue),
        BodyReader,
        NodeFactory=NodeMaker,
    )
    RootsValue = tuple(ReadNodeMut(ReaderValue) for _ in range(CountValue))
    FieldsValue = ReadMbsMut(ContextValue, ReaderValue, FindModelRoot(SeedValue))
    if Cursor.GetRemaining():
        raise BodyUnsupported(
            f"resolved graph has {Cursor.GetRemaining()} trailing bytes"
        )
    if SavedSweep:
        if FieldsValue != {"n": 0, "fcd8": []}:
            raise BodyUnsupported(
                "saved SOLIDWORKS sweep has alternate configuration body mappings"
            )
        CheckSweepUse(ContextValue)
    if ReadEllipses:
        CheckEllipUse(ContextValue)
    ContextValue.UsageValue.IsComplete = True
    return ResolvedGraph(
        RootsValue,
        FieldsValue,
        ReaderValue.MapValue.Snapshot(),
        BaseValue,
        VersionValue,
        dict(LinkContext),
        GetBodyReport(ContextValue.UsageValue),
    )
