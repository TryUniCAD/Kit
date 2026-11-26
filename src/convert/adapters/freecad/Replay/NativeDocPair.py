from __future__ import annotations

import hashlib as Hashlib

from convert.adapters.freecad.Replay.NativeIdentity import IsNativeDoc, IsNativeDocA
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.document.Models.DocumentModel import CadDocument


# this definition exists because focused behavior needs one stable owner
def NativeDocPair(DocValue: CadDocument) -> tuple[BrepPayload, BrepPayload] | None:
    Documents = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDoc(Payload))
    )
    Bindings = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDocA(Payload))
    )
    if len(Documents) != 1 or len(Bindings) != 1:
        return None
    NativeDoc = Documents[0]
    Binding = Bindings[0]
    try:
        NativeDigest = bytes.fromhex(NativeDoc.sha256)
    except ValueError:
        return None
    if len(NativeDigest) != Hashlib.sha256().digest_size:
        return None
    if (
        NativeDoc.data is None
        or Hashlib.sha256(NativeDoc.data).digest() != NativeDigest
        or Binding.data != NativeDigest
        or (Binding.sha256 != Hashlib.sha256(NativeDigest).hexdigest())
    ):
        return None
    return (NativeDoc, Binding)
