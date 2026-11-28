from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Selection import SelectPathElem, Selection


# a real sketch entity path must preserve selected axis identity independently of cached line geometry
def MakeRevSelect(LinkValue: NativeLink, OwnerValue: RevolveOwner) -> Selection:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    AxisValue = OwnerValue.ProfileGraph.AxisValue
    FrameValue = OwnerValue.FrameValue
    return Selection(
        id=f"sldprt:selection:{NativeId}:axis",
        name=ReadNativeName(OwnerValue.NodeValue) + " axis",
        path=(
            SelectPathElem("sketch", f"sldprt:sketch:{ProfileId}"),
            SelectPathElem(
                "sketch_entity",
                f"sldprt:sketch:{ProfileId}:line:{AxisValue.PermanentId}",
            ),
        ),
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, OwnerValue.AxisValue.WrapperValue),
            str(AxisValue.PermanentId),
        ),
        attributes=FreezeMapping(
            {
                "native_owner_id": NativeId,
                "native_axis_array_index": AxisValue.IndexValue,
                "native_line_creation_id": AxisValue.CreationId,
                "native_axis_permanent_mark": AxisValue.PermanentId,
                "native_selected_handle_index": OwnerValue.AxisValue.HandleValue.IndexValue,
                "native_ordered_endpoints_mm": (
                    (
                        FrameValue.StartValue.x,
                        FrameValue.StartValue.y,
                        FrameValue.StartValue.z,
                    ),
                    (
                        FrameValue.EndValue.x,
                        FrameValue.EndValue.y,
                        FrameValue.EndValue.z,
                    ),
                ),
                "native_reverse_direction": OwnerValue.IsReverse,
                "topology_role": "revolution_construction_axis",
            }
        ),
    )
