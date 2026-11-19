from __future__ import annotations

from dataclasses import replace as Replace

from convert.adapters.freecad.Replay.NativeIdentity import (
    KExplicitSketchProfile,
    KReplaySemanticAttr,
    KReplaySketchAttr,
)
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.document.Models.DocumentModel import CadDocument


# replay proof belongs to the verified archive envelope and can be retired independently
def SetReplayDigest(
    DocValue: CadDocument, NativeDoc: BrepPayload, Digest: str | None
) -> CadDocument:
    Attributes = {**NativeDoc.attributes, KReplaySketchAttr: KExplicitSketchProfile}
    if Digest is None:
        Attributes.pop(KReplaySemanticAttr, None)
    else:
        Attributes[KReplaySemanticAttr] = Digest
    Updated = Replace(NativeDoc, attributes=Attributes)
    return Replace(
        DocValue,
        brep_payloads=tuple(
            Updated if Payload is NativeDoc else Payload
            for Payload in DocValue.brep_payloads
        ),
    )
