from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# design only reads keep validated body lineage without exposing hidden geometry or dangling payload references
def StripEqGeom(Document: CadDocument) -> CadDocument:
    (BodyValue,) = Document.bodies
    Attributes = dict(BodyValue.attributes)
    Attributes["parasolid_payload_ids"] = ()
    _ = Attributes.pop("parasolid_active_payload_id", None)
    Metadata = dict(Document.metadata)
    Proof = Metadata.get("solidworks.native_body_names")
    if isinstance(Proof, Mapping):
        Summary = FreezeMapping(
            {**CastValue(Mapping[str, object], Proof), "complete_brep_binding": False}
        )
        Attributes["solidworks.native_body"] = Summary
        Metadata["solidworks.native_body_names"] = Summary
    return ReplaceValue(
        Document,
        brep=None,
        brep_payloads=(),
        bodies=(ReplaceValue(BodyValue, attributes=FreezeMapping(Attributes)),),
        metadata=FreezeMapping(Metadata),
    )
