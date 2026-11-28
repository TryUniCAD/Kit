from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# semantic coverage must identify measured owners without implying complete document tree or writer qualification
def ReportRevolve(
    LinkValue: NativeLink, OwnerValue: RevolveOwner
) -> Mapping[str, object]:
    NormalValue = OwnerValue.FrameValue.SupportValue.z_axis
    PlaneName = "front"
    if NormalValue.z != 1.0:
        PlaneName = "top" if NormalValue.y == 1.0 else "right"
    return {
        "feature_id": NativeNodeId(OwnerValue.NodeValue),
        "profile_id": NativeNodeId(OwnerValue.ProfileValue),
        "parameter_name": OwnerValue.AngleValue.NameValue,
        "angle_radians": OwnerValue.AngleValue.RadiansValue,
        "reverse_direction": OwnerValue.IsReverse,
        "axis_array_index": OwnerValue.AxisValue.IndexValue,
        "axis_permanent_mark": OwnerValue.AxisValue.MarkValue,
        "axis_creation_id": OwnerValue.ProfileGraph.AxisValue.CreationId,
        "contour_lines": len(OwnerValue.ProfileGraph.LoopValue.LinesValue),
        "contour_axis_relations": len(OwnerValue.ProfileGraph.AxisRules),
        "axis_solver_relations": (),
        "native_solver_status_measured": False,
        "feature_owner": NativeNodeSpan(LinkValue, OwnerValue.NodeValue),
        "parameter_owner": OwnerValue.AngleValue.OwnerValue,
        "axis_owner": NativeNodeSpan(LinkValue, OwnerValue.AxisValue.WrapperValue),
        "scope": f"ordinary_modern_single_blind_rectangular_boss_{PlaneName}_upward_axis",
        "full_native_tree_qualified": False,
        "public_writer_qualified": False,
    }
