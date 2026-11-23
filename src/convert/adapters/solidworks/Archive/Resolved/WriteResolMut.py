from collections.abc import Callable, Mapping, MutableMapping
from functools import partial as BindArgs

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.CheckEllipUse import CheckEllipUse
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSavedSwMut import (
    UseSavedSwMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSweepCtxMut import (
    UseSweepCtxMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.WriteSwSchema import (
    CheckSweepUse,
    WriteSwSchema,
)
from convert.adapters.solidworks.Archive.Resolved.UseChmfCtxMut import UseChmfCtxMut
from convert.adapters.solidworks.Archive.Resolved.UseEllipCtxMut import UseEllipCtxMut
from convert.adapters.solidworks.Archive.Resolved.UseShellCtxMut import UseShellCtxMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# scoped feature layouts cannot be combined across incompatible resolved contexts
def UseWriteCtxMut(
    ContextValue: BodyContext,
    ExtraFields: MutableMapping[str, object] | None,
    *,
    ReplayEllipses: bool,
    WriteChamfers: bool,
    WriteSweeps: bool,
    WriteShell: bool,
    ReplaySavedSweep: bool,
) -> Callable[[BodyWriter, ArchiveNode], None]:
    HasSweep = WriteSweeps or ReplaySavedSweep
    if WriteShell:
        if ReplayEllipses or WriteChamfers or HasSweep:
            raise BodyUnsupported(
                "SOLIDWORKS shell requires its exclusive archive scope"
            )
        UseShellCtxMut(ContextValue)
    if HasSweep:
        ExpectedFields: dict[str, object] | None = (
            {"n": 0, "fcd8": []} if ReplaySavedSweep else None
        )
        if not ReplaySavedSweep and (
            ReplayEllipses or WriteChamfers or ExtraFields is not None
        ):
            raise BodyUnsupported(
                "cold sweep requires its exclusive ordinary resolved context"
            )
        if ReplaySavedSweep and (ReplayEllipses or WriteChamfers or WriteSweeps):
            raise BodyUnsupported("SOLIDWORKS sweep requires its own archive scope")
        if ReplaySavedSweep and ExtraFields != ExpectedFields:
            raise BodyUnsupported(
                "SOLIDWORKS sweep has alternate configuration body mappings"
            )
        (UseSavedSwMut if ReplaySavedSweep else UseSweepCtxMut)(ContextValue)
        return BindArgs(
            WriteBodyMut,
            SchemaWriter=BindArgs(WriteSwSchema, SavedResult=ReplaySavedSweep),
        )
    if ReplayEllipses:
        UseEllipCtxMut(ContextValue)
    if WriteChamfers:
        UseChmfCtxMut(ContextValue)
    return WriteBodyMut


# resolved emission allocates only new graph members after the original configuration map prefix
def WriteResolMut(
    RootsValue: tuple[ArchiveNode | None, ...],
    ExtraFields: MutableMapping[str, object] | None,
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    *,
    UsageValue: BodyUsage | None = None,
    ReplayEllipses: bool = False,
    WriteChamfers: bool = False,
    WriteSweeps: bool = False,
    WriteShell: bool = False,
    ReplaySavedSweep: bool = False,
) -> tuple[bytes, ResolvedGraph]:
    ContextValue = MakeResolvedCtx(VersionValue, SeedValue, LinkContext, UsageValue)
    BodyWriterValue = UseWriteCtxMut(
        ContextValue,
        ExtraFields,
        ReplayEllipses=ReplayEllipses,
        WriteChamfers=WriteChamfers,
        WriteSweeps=WriteSweeps,
        WriteShell=WriteShell,
        ReplaySavedSweep=ReplaySavedSweep,
    )
    _ = NormalizeCount(len(RootsValue), "")
    WriterValue = BodyWriter(
        ArchiveMaps(SeedValue.CounterValue, SeedValue),
        ContextValue,
        BodyWriterValue,
    )
    WriterValue.OutputValue.extend(EncodeScalar(SeedValue.CounterValue, "u32"))
    WriterValue.OutputValue.extend(EncodeCount(len(RootsValue)))
    for NodeValue in RootsValue:
        WriteNodeMut(WriterValue, NodeValue)
    WriteMbsMut(WriterValue, FindModelRoot(SeedValue), ExtraFields)
    if ReplayEllipses:
        CheckEllipUse(ContextValue)
    if WriteSweeps or ReplaySavedSweep:
        CheckSweepUse(ContextValue)
    ContextValue.UsageValue.IsComplete = True
    GraphValue = ResolvedGraph(
        RootsValue,
        ExtraFields,
        WriterValue.MapValue.Snapshot(),
        SeedValue.CounterValue,
        VersionValue,
        dict(LinkContext),
        GetBodyReport(ContextValue.UsageValue),
    )
    return bytes(WriterValue.OutputValue), GraphValue
