from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import (
    KRefSupportSource,
    NativeModel,
    NativeSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdDatum import (
    ReadColdDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# portable contours must reuse the actual support and its separately proven stock or tool
def BindColdProfile(
    SketchValue: NativeSketch,
    OwnerValue: ExtrudeOwner,
    OwnersValue: ColdStockOwners,
    Features: dict[int, ArchiveNode],
    Model: NativeModel,
) -> NativeSketch:
    LinkValue = OwnersValue.LinkValue
    ProfileValue = OwnerValue.ProfileValue
    FrameValue, DatumValue = ReadColdDatum(LinkValue, ProfileValue, Features)
    DatumId = NativeNodeId(DatumValue)
    Plane = next((Value for Value in Model.planes if Value.object_id == DatumId), None)
    if (
        Plane is None
        or (FrameValue.origin.x, FrameValue.origin.y, FrameValue.origin.z)
        != Plane.origin_mm
        or (FrameValue.x_axis.x, FrameValue.x_axis.y, FrameValue.x_axis.z)
        != Plane.u_axis
        or (FrameValue.y_axis.x, FrameValue.y_axis.y, FrameValue.y_axis.z)
        != Plane.v_axis
        or (FrameValue.z_axis.x, FrameValue.z_axis.y, FrameValue.z_axis.z)
        != Plane.normal
    ):
        raise ValueError("typed stock support contradicts its public datum")
    Bound = ReplaceValue(
        SketchValue,
        support_plane_id=DatumId,
        support_source=KRefSupportSource,
        unframed_support_plane_id=None,
        TypedFrame=FrameValue,
        dimensions=(),
        constraints=(),
    )
    if OwnerValue is not OwnersValue.CutValue:
        return ReplaceValue(Bound, TypedLines=ReadThruStock(ProfileValue, LinkValue))
    SketchNode = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    ToolValue = ReadLocalCirc(SketchNode, LinkValue, AllowFree=True)
    if ToolValue is None or ToolValue[1] is not None:
        raise ValueError("two-stock tool does not own a free circle")
    return ReplaceValue(Bound, TypedCircle=ToolValue[0])
