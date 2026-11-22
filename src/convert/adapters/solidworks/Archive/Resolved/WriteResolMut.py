from collections.abc import Mapping, MutableMapping

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.UseChmfCtxMut import UseChmfCtxMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# resolved emission allocates only new graph members after the original configuration map prefix
def WriteResolMut(
    RootsValue: tuple[ArchiveNode | None, ...],
    ExtraFields: MutableMapping[str, object] | None,
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    *,
    UsageValue: BodyUsage | None = None,
    WriteChamfers: bool = False,
) -> tuple[bytes, ResolvedGraph]:
    ContextValue = MakeResolvedCtx(
        VersionValue, SeedValue, LinkContext, UsageValue, ChamferLayout=WriteChamfers
    )
    if WriteChamfers:
        UseChmfCtxMut(ContextValue)
    _ = NormalizeCount(len(RootsValue), "")
    WriterValue = BodyWriter(
        ArchiveMaps(SeedValue.CounterValue, SeedValue), ContextValue, WriteBodyMut
    )
    WriterValue.OutputValue.extend(EncodeScalar(SeedValue.CounterValue, "u32"))
    WriterValue.OutputValue.extend(EncodeCount(len(RootsValue)))
    for NodeValue in RootsValue:
        WriteNodeMut(WriterValue, NodeValue)
    WriteMbsMut(WriterValue, FindModelRoot(SeedValue), ExtraFields)
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
