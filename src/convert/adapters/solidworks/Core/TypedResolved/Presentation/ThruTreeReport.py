from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# the new source profile must expose exact containment without implying complete presentation conversion or native acceptance
def ThruTreeReport(
    Model: NativeModel,
    RootsValue: tuple[ArchiveNode, ...],
    RowsValue: tuple[Mapping[str, object], ...],
    MembersValue: tuple[ArchiveNode, ...],
    HelpersValue: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    return {
        "status": "ordinary_through_all_source_profile",
        "rows": RowsValue,
        "configuration_helpers": HelpersValue,
        "retained_public_ids": tuple(Value.object_id for Value in Model.features),
        "root_ids": tuple(NativeNodeId(Value) for Value in RootsValue),
        "member_ids": tuple(NativeNodeId(Value) for Value in MembersValue),
        "public_timeline_preserved": True,
        "parametric_timeline_stable": False,
        "profile": "solidworks_2026_english_saved_selected_through_cut",
        "comparison_scope": ("identity", "name", "type", "parent", "order"),
        "implicit_default_state_encoded": False,
        "native_status_flags_qualified": False,
        "arbitrary_session_defaults_qualified": False,
        "custom_tree_layouts_qualified": False,
        "authored_caption_parity_qualified": False,
        "full_native_tree_qualified": False,
        "source_conversion_qualified": False,
        "provenance_qualified": False,
        "continuous_automatic_scope_qualified": False,
    }
