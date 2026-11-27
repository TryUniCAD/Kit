from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CopyPlacement import (
    CopyPlacement,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.EndpointData import (
    EndpointData,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import (
    WrapperFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a resolved wrapper combines the actual child reference with independently computed world plane and placement caches
def MakeResolved(Endpoint: EndpointData) -> ArchiveNode:
    Fields = WrapperFields(Endpoint.ReferenceValue)
    Fields.update(
        {
            "f08": SignedStamp(Endpoint.UpdateValue),
            "f10": CopyPlacement(Endpoint.PlacementValue),
            "f18": CopyPlacement(Endpoint.PlacementValue),
            "fd0": dict(
                zip(("x", "y", "z"), Endpoint.FrameValue.OriginValue, strict=True)
            ),
            "fe8": dict(
                zip(("x", "y", "z"), Endpoint.FrameValue.NormalValue, strict=True)
            ),
            "f100": FrameXform(Endpoint.FrameValue),
            "f68": 1,
            "has_f10": 1,
            "has_f18": 1,
            "f0c": Endpoint.ConfigId,
            "f188": dict.fromkeys(("x", "y", "z"), 0.0),
        }
    )
    Fields.update(
        dict(zip(("fb0", "fb8", "fc0", "fc8"), Endpoint.BordersValue, strict=True))
    )
    return ArchiveNode(RuntimeClass("moPlaneRef_w", 1), Fields)
