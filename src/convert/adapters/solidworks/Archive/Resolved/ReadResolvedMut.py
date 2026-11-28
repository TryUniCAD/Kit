from collections.abc import Callable, Mapping
from functools import partial as PartialValue

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
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.ReadMbsMut import ReadMbsMut
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSavedSwMut import (
    UseSavedSwMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.ReadSwSchema import (
    ReadSwSchema,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSweepCtxMut import (
    UseSweepCtxMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.WriteSwSchema import (
    CheckSweepUse,
)


# resolved features extend the exact configuration snapshot after verifying the stored inherited base
def ReadResolvedMut(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    *,
    UsageValue: BodyUsage | None = None,
    NodeMaker: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None,
    ReadSweeps: bool = False,
    SavedSweep: bool = False,
) -> ResolvedGraph:
    ContextValue = MakeResolvedCtx(
        VersionValue, SeedValue, LinkContext, UsageValue, SavedSweep=SavedSweep
    )
    if SavedSweep:
        UseSavedSwMut(ContextValue)
    elif ReadSweeps:
        UseSweepCtxMut(ContextValue)
    SchemaReader = (
        PartialValue(ReadSwSchema, SavedResult=SavedSweep)
        if ReadSweeps or SavedSweep
        else None
    )
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
        PartialValue(ReadBodyMut, ContextValue, SchemaReader=SchemaReader),
        NodeFactory=NodeMaker,
    )
    RootsValue = tuple(ReadNodeMut(ReaderValue) for _ in range(CountValue))
    FieldsValue = ReadMbsMut(ContextValue, ReaderValue, FindModelRoot(SeedValue))
    if SavedSweep and FieldsValue != {"n": 0, "fcd8": []}:
        raise BodyUnsupported(
            "saved SOLIDWORKS sweep has alternate configuration body mappings"
        )
    if ReadSweeps or SavedSweep:
        CheckSweepUse(ContextValue)
    if Cursor.GetRemaining():
        raise BodyUnsupported(
            f"resolved graph has {Cursor.GetRemaining()} trailing bytes"
        )
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
