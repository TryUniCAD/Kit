from collections.abc import Callable
from functools import partial as PartialValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Mates.MakeMatesCtx import MakeMatesCtx
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Mates.RequireMates import RequireMates
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# populated mate objects continue the resolved map instead of inventing reference placeholders
def ReadMatesMut(
    BufferValue: bytes,
    ResolvedValue: ResolvedGraph,
    *,
    UsageValue: BodyUsage | None = None,
    NodeMaker: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None,
) -> MatesGraph:
    ContextValue = MakeMatesCtx(ResolvedValue, UsageValue)
    Cursor = BinaryReader(BufferValue)
    BaseValue = int.from_bytes(Cursor.TakeBytes(4), "little", signed=True)
    if BaseValue != ResolvedValue.MapValue.CounterValue:
        raise BodyUnsupported(
            "mate list prefix differs from its actual resolved snapshot"
        )
    CountValue, Cursor.OffsetValue = ReadCount(Cursor.BytesValue, Cursor.OffsetValue)
    CountValue = NormalizeCount(CountValue, "")
    ReaderValue = GraphReader(
        Cursor,
        ArchiveMaps(BaseValue, ResolvedValue.MapValue),
        PartialValue(ReadBodyMut, ContextValue),
        NodeFactory=NodeMaker,
    )
    RootsValue = tuple(ReadNodeMut(ReaderValue) for _ in range(CountValue))
    RequireMates(RootsValue)
    if Cursor.GetRemaining():
        raise BodyUnsupported(f"mate list has {Cursor.GetRemaining()} trailing bytes")
    ContextValue.UsageValue.IsComplete = True
    return MatesGraph(
        CastValue(tuple[ArchiveNode, ...], RootsValue),
        ReaderValue.MapValue.Snapshot(),
        BaseValue,
        ResolvedValue.VersionValue,
        dict(ResolvedValue.ContextValue),
        GetBodyReport(ContextValue.UsageValue),
    )
