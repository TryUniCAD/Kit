from __future__ import annotations

from convert.adapters.freecad.Replay.ApplyChildren import ApplyChildren
from convert.adapters.freecad.Replay.ApplySketchFlag import ApplySketchFlag
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.NativeIdentity import KReplaySemanticAttr
from convert.adapters.freecad.Replay.SemanticDigest import SemanticDigest
from convert.adapters.freecad.Replay.SetReplayDigest import SetReplayDigest
from interchange.document.Models.DocumentModel import CadDocument


# advance only a proven historical baseline so reopened edits keep their intended suppression
def ApplyFlags(
    Before: CadDocument, After: CadDocument, DocValue: CadDocument
) -> CadDocument:
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return DocValue
    NativeDoc, _ = PairValue
    if not NativeDoc.sha256 == Before.source.sha256 == After.source.sha256:
        return DocValue
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    if Expected != SemanticDigest(Before):
        return DocValue
    Current = SemanticDigest(After)
    if Expected == Current:
        return DocValue
    Updated = SetReplayDigest(
        ApplySketchFlag(DocValue, Before, After), NativeDoc, Current
    )
    return ApplyChildren(Updated, Before, After, ApplyFlags)
