from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Selection import SelectPathElem, Selection


# actual datum selections retain both the neutral path and the linked wrapper location
def MakeTiltPick(
    LinkValue: NativeLink,
    NativeOwner: ArchiveNode,
    NativeTarget: ArchiveNode,
    WrapperValue: ArchiveNode,
    RoleValue: str,
    IsPlane: bool,
) -> Selection:
    OwnerId, TargetId = NativeNodeId(NativeOwner), NativeNodeId(NativeTarget)
    PickId = f"sldprt:selection:{OwnerId}:{RoleValue}"
    KindValue = "support_plane" if IsPlane else "feature"
    TargetKey = f"sldprt:{'plane' if IsPlane else 'feature'}:{TargetId}"
    return Selection(
        PickId,
        ReadNativeName(NativeTarget),
        (SelectPathElem(KindValue, TargetKey),),
        query=FreezeMapping(
            {
                "native_owner_id": OwnerId,
                "native_target_id": TargetId,
                "topology_role": RoleValue,
            }
        ),
        provenance=TypedProvenance(NativeNodeSpan(LinkValue, WrapperValue), PickId),
    )
