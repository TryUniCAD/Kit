from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# semantic evidence must distinguish owned fields from unpromoted geometry tree rows and mate streams
def ReportTyped(
    Model: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    OwnersValue: Mapping[int, ExtrudeOwner],
    CircleIds: tuple[int, ...],
    LineIds: tuple[int, ...] = (),
) -> Mapping[str, object]:
    LegacyIds = {Feature.object_id for Feature in Model.features}
    return {
        "status": "supplemented",
        "archive_version": LinkValue.ResolvedValue.VersionValue,
        "configuration_id": 0,
        "model_class": LinkValue.ConfigValue.RootValue.ClassValue.NameValue,
        "map_base": LinkValue.ResolvedValue.MapBase,
        "map_counter": LinkValue.ResolvedValue.MapValue.CounterValue,
        "feature_identities": tuple(sorted(LegacyIds.intersection(Features))),
        "legacy_only_feature_ids": tuple(sorted(LegacyIds.difference(Features))),
        "typed_only_feature_ids": tuple(sorted(set(Features).difference(LegacyIds))),
        "extrusions": tuple(
            {
                "feature_id": NativeId,
                "profile_id": NativeNodeId(OwnerValue.ProfileValue),
                "parent_ids": tuple(
                    NativeNodeId(NodeValue) for NodeValue in OwnerValue.ParentsValue
                ),
                "parameter_name": OwnerValue.DepthValue.DepthValue.name,
                "depth_m": OwnerValue.DepthValue.DepthValue.native_value,
                "parameter_owner": OwnerValue.DepthValue.DepthValue.TypedOwner,
            }
            for NativeId, OwnerValue in OwnersValue.items()
        ),
        "semantic_fields": ("feature_id", "feature_name", "feature_class")
        + (("blind_profile", "blind_depth") if OwnersValue else ())
        + (
            ("closed_circle", "radial_dimension", "fixed_circle_center")
            if CircleIds
            else ()
        )
        + (("closed_line_loop", "line_endpoints", "line_handles") if LineIds else ()),
        **({"line_loop_profiles": LineIds} if LineIds else {}),
        **({"circle_profiles": CircleIds} if CircleIds else {}),
        "usage": LinkValue.ResolvedValue.ReportValue,
        "full_linked_graph": False,
        "typed_geometry_projection": bool(CircleIds or LineIds),
        "typed_assembly_mates": False,
        "public_writer_qualified": False,
    }
