from collections.abc import Mapping
from typing import cast as CastValue

from interchange import CadDocument


# ordinary presentation rows must be honest about implicit identity and must not become extra modeling steps
def AssertTreeRead(Document: CadDocument) -> None:
    GraphValue = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    TreeValue = CastValue(Mapping[str, object], GraphValue["native_tree"])
    assert TreeValue["status"] == "ordinary_default_profile"
    RowsValue = CastValue(tuple[Mapping[str, object], ...], TreeValue["rows"])
    assert len(RowsValue) == 25 and len(Document.feature_timeline) == 19
    Members = tuple(RowValue for RowValue in RowsValue if RowValue["parent_id"])
    assert len(Members) == 6
    assert all(RowValue["native_object_id"] is None for RowValue in Members)
    assert all(RowValue["state"] is None for RowValue in Members)
    assert all(RowValue["typed_archive_owner"] is None for RowValue in Members)
    assert tuple(RowValue["owner_role"] for RowValue in Members) == (
        "notes.head",
        "notes.end",
        "light.ambient",
        "light.directional.1",
        "light.directional.2",
        "light.directional.3",
    )
    assert tuple(
        Feature.attributes["native_type"] for Feature in Document.feature_timeline
    ) == tuple(RowValue["type"] for RowValue in RowsValue if not RowValue["parent_id"])
    assert TreeValue["configuration_helpers"] == ()
    assert (
        TreeValue["native_status_flags_qualified"]
        is TreeValue["arbitrary_session_defaults_qualified"]
        is TreeValue["custom_tree_layouts_qualified"]
        is TreeValue["full_native_tree_qualified"]
        is False
    )
