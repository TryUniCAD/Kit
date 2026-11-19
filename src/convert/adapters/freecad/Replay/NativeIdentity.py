from __future__ import annotations

from convert.adapters.freecad.Format import KInfoValue as InfoValue
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole

# this binding exists because shared behavior needs one stable value
KNativeDocId = "freecad:native-document"

# this binding exists because shared behavior needs one stable value
KNativeDocBindingId = "freecad:native-document-binding"

# this binding exists because shared behavior needs one stable value
KReplaySemanticAttr = "freecad.replay_semantic_sha256"

# projection identity separates newly authored flags from historical visibility defaults
KReplaySketchAttr = "freecad.replay_sketch_profile"

# the current profile records explicit native suppression separately from display visibility
KExplicitSketchProfile = "explicit-suppression"


# this definition exists because focused behavior needs one stable owner
def IsNativeDoc(Payload: BrepPayload) -> bool:
    return (
        Payload.id == KNativeDocId
        and Payload.format_id == InfoValue.format_id
        and (Payload.kind == "native_document")
        and (Payload.role == PayloadRole.DOCUMENT)
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeDocA(Payload: BrepPayload) -> bool:
    return (
        Payload.id == KNativeDocBindingId
        and Payload.format_id == f"{InfoValue.format_id}.sha256"
        and (Payload.kind == "native_document_binding")
        and (Payload.schema == "sha256")
        and (Payload.role == PayloadRole.VERIFICATION)
    )


# this definition exists because focused behavior needs one stable owner
def IsNative(Payload: BrepPayload) -> bool:
    return IsNativeDoc(Payload) or IsNativeDocA(Payload)
