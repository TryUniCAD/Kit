from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch


# a newly supported principal sketch must keep the same datum and transform as its selected world axis
def CheckRevSupport(
    DocumentValue: CadDocument, SketchValue: Sketch, OwnerValue: RevolveOwner,
    *, CheckFront: bool = False,
) -> None:
    FrameValue = OwnerValue.FrameValue.SupportValue
    if FrameValue.z_axis.z == 1.0 and not CheckFront:
        return
    Reference = RequireNative(
        OwnerValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    Identity = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    PlaneId = f"sldprt:plane:{Identity}"
    PlanesValue = tuple(
        Value for Value in DocumentValue.support_planes if Value.id == PlaneId
    )
    if (
        SketchValue.support_plane_id != PlaneId
        or len(PlanesValue) != 1
        or PlanesValue[0].transform != FrameValue
    ):
        raise ValueError(
            "ordinary revolve public support differs from its actual datum"
        )
