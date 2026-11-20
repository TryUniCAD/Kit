from __future__ import annotations

from collections.abc import Callable

from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.PrepareChildren import PrepareChildren
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from convert.adapters.freecad.Replay.SetReplayDigest import SetReplayDigest
from interchange.document.Models.DocumentModel import CadDocument


# an independent child repair invalidates the previous semantic baseline of the parent
def PrepareLinked(
    DocValue: CadDocument,
    InitialDigest: str | None,
    PrepareBranch: Callable[[CadDocument], CadDocument] | None,
    ReplayBytes: bytes | None = None,
) -> tuple[CadDocument, bytes | None]:
    if PrepareBranch is None:
        return DocValue, ReplayBytes
    Prepared = PrepareChildren(DocValue, PrepareBranch)
    if InitialDigest is None or SemanticDigest(Prepared) == InitialDigest:
        return Prepared, ReplayBytes
    PairValue = NativeDocPair(Prepared)
    if PairValue is not None:
        Prepared = SetReplayDigest(Prepared, PairValue[0], None)
    return Prepared, None
