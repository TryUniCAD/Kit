from __future__ import annotations

from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from convert.adapters.freecad.Replay.SetReplayDigest import SetReplayDigest
from interchange.document.Models.DocumentModel import CadDocument


# only freshly parsed native model values establish a current baseline for this document
def AnnotateNative(DocValue: CadDocument) -> CadDocument:
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return DocValue
    NativeDoc, _ = PairValue
    return SetReplayDigest(DocValue, NativeDoc, SemanticDigest(DocValue))
