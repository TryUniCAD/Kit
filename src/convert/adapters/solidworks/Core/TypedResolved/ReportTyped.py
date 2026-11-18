from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Ends.ReportEndFields import (
    ReportEndFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Units.ReportPartUnits import (
    ReportPartUnits,
)


# semantic evidence must distinguish owned fields from unpromoted geometry tree rows and mate streams
def ReportTyped(
    Model: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    OwnersValue: Mapping[int, ExtrudeOwner],
    CircleIds: tuple[int, ...],
    LineIds: tuple[int, ...] = (),
    BodyEvidence: Mapping[str, object] | None = None,
    FreeCircleIds: tuple[int, ...] = (),
) -> Mapping[str, object]:
    LegacyIds = {Feature.object_id for Feature in Model.features}
    return {
        **ReportPartUnits(LinkValue.ConfigValue.RootValue),
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
                **ReportEndFields(OwnerValue),
                **(
                    {"end_owner": NativeNodeSpan(LinkValue, OwnerValue.EndValue)}
                    if OwnerValue.DepthValue is None
                    else {}
                ),
            }
            for NativeId, OwnerValue in OwnersValue.items()
        ),
        "semantic_fields": ("feature_id", "feature_name", "feature_class")
        + (
            ("extrusion_profile", "extrusion_end", "driving_depth")
            if OwnersValue
            else ()
        )
        + (
            ("depthless_extrusion_end",)
            if any(Owner.DepthValue is None for Owner in OwnersValue.values())
            else ()
        )
        + (("closed_circle",) if CircleIds or FreeCircleIds else ())
        + (("radial_dimension", "fixed_circle_center") if CircleIds else ())
        + (("closed_line_loop", "line_endpoints", "line_handles") if LineIds else ())
        + (("consumed_body_producer", "cut_body_scope") if BodyEvidence else ()),
        **({"line_loop_profiles": LineIds} if LineIds else {}),
        **(
            {"circle_profiles": (*CircleIds, *FreeCircleIds)}
            if CircleIds or FreeCircleIds
            else {}
        ),
        **({"free_circle_profiles": FreeCircleIds} if FreeCircleIds else {}),
        **({"cut_body_dependency": BodyEvidence} if BodyEvidence else {}),
        "usage": LinkValue.ResolvedValue.ReportValue,
        "full_linked_graph": False,
        "typed_geometry_projection": bool(CircleIds or FreeCircleIds or LineIds),
        "typed_assembly_mates": False,
        "public_writer_qualified": False,
    }
