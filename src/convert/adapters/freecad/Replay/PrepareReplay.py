from __future__ import annotations

from functools import partial as Partial

from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.PrepareBound import PrepareBound
from convert.adapters.freecad.Replay.PrepareLinked import PrepareLinked
from convert.adapters.freecad.Replay.ReadCache import KReplayReadCache
from interchange.document.Models.DocumentModel import CadDocument


# each embedded child has its own archive binding and historical digest
def PrepareChild(DocValue: CadDocument, ReplayReads: KReplayReadCache) -> CadDocument:
    return PrepareReplay(DocValue, Migrate=True, ReplayReads=ReplayReads)[0]


# write requests share archive verification between exact replay and legacy sketch migration
def PrepareReplay(
    DocValue: CadDocument, *, Migrate: bool, ReplayReads: KReplayReadCache | None = None
) -> tuple[CadDocument, bytes | None]:
    if ReplayReads is None:
        ReplayReads = {}
    PrepareBranch = Partial(PrepareChild, ReplayReads=ReplayReads) if Migrate else None
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return PrepareLinked(DocValue, None, PrepareBranch)
    return PrepareBound(DocValue, PairValue[0], ReplayReads, PrepareBranch)
