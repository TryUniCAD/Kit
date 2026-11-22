from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import KRefSupportSource, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# the actual support reference supersedes the provisional plane from keyword discovery
def BindColdSketch(ModelValue: NativeModel, OwnerValue: RevolveOwner) -> NativeModel:
    Reference = RequireNative(
        OwnerValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(PlaneId) is not int:
        raise ValueError("cache-free revolve requires its actual native support")
    (SketchValue,) = ModelValue.sketches
    return ReplaceValue(
        ModelValue,
        sketches=(
            ReplaceValue(
                SketchValue,
                support_plane_id=PlaneId,
                support_plane=None,
                support_source=KRefSupportSource,
                unframed_support_plane_id=None,
                TypedFrame=OwnerValue.FrameValue.SupportValue,
            ),
        ),
    )
