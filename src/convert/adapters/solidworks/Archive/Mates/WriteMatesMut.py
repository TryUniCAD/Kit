from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Mates.MakeMatesCtx import MakeMatesCtx
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Mates.RequireMates import RequireMates
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# native list framing writes the real inherited counter before storing its current graph objects
def WriteMatesMut(
    RootsValue: tuple[ArchiveNode, ...],
    ResolvedValue: ResolvedGraph,
    *,
    UsageValue: BodyUsage | None = None,
) -> tuple[bytes, MatesGraph]:
    ContextValue = MakeMatesCtx(ResolvedValue, UsageValue)
    RequireMates(RootsValue)
    _ = NormalizeCount(len(RootsValue), "")
    SeedValue = ResolvedValue.MapValue
    WriterValue = BodyWriter(
        ArchiveMaps(SeedValue.CounterValue, SeedValue), ContextValue, WriteBodyMut
    )
    WriterValue.OutputValue.extend(EncodeScalar(SeedValue.CounterValue, "i32"))
    WriterValue.OutputValue.extend(EncodeCount(len(RootsValue)))
    for NodeValue in RootsValue:
        WriteNodeMut(WriterValue, NodeValue)
    ContextValue.UsageValue.IsComplete = True
    GraphValue = MatesGraph(
        RootsValue,
        WriterValue.MapValue.Snapshot(),
        SeedValue.CounterValue,
        ResolvedValue.VersionValue,
        dict(ResolvedValue.ContextValue),
        GetBodyReport(ContextValue.UsageValue),
    )
    return bytes(WriterValue.OutputValue), GraphValue
