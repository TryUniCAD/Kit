from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord
from interchange.document.Models.DocumentModel import CadDocument


# presentation evidence must still identify every actual public source owner before geometry can be projected independently
def ReadSourceTree(DocumentValue: CadDocument) -> Mapping[str, object]:
    Evidence = RequireRecord(
        DocumentValue.metadata.get("solidworks.typed_resolved_semantics")
    )
    TreeValue = RequireRecord(Evidence.get("native_tree"))
    Retained = TreeValue.get("retained_public_ids")
    if not isinstance(Retained, (tuple, list)):
        raise ValueError("source presentation lacks its actual retained identities")
    IdValues = CastValue(tuple[object, ...] | list[object], Retained)
    if (
        Evidence.get("archive_version") != 19000
        or TreeValue.get("status") != "ordinary_through_all_source_profile"
        or TreeValue.get("public_timeline_preserved") is not True
        or tuple(IdValues)
        != tuple(
            Value.attributes.get("native_object_id")
            for Value in DocumentValue.feature_timeline
        )
    ):
        raise ValueError("source presentation ownership is incomplete or stale")
    return TreeValue
