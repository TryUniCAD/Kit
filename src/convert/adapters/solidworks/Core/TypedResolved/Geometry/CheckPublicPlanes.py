from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel


# analytic geometry requires that each projected datum retain the exact typed frame
def CheckPlanes(ModelValue: NativeModel, Features: Mapping[int, ArchiveNode]) -> None:
    PlaneIds = {
        Identity
        for Identity, NodeValue in Features.items()
        if NodeValue.ClassValue.NameValue == "moRefPlane_c"
    }
    if (
        len(ModelValue.planes) != len(PlaneIds)
        or {Plane.object_id for Plane in ModelValue.planes} != PlaneIds
    ):
        raise ValueError("cache free prism public plane inventory is incomplete")
    for Plane in ModelValue.planes:
        FrameValue, _ = ReadDatumFrame(Features[Plane.object_id])
        if Plane.origin_mm != tuple(
            Value * 1000 for Value in FrameValue.OriginValue
        ) or (Plane.u_axis, Plane.v_axis, Plane.normal) != (
            FrameValue.AxisU,
            FrameValue.AxisV,
            FrameValue.NormalValue,
        ):
            raise ValueError(
                "cache free prism public placement differs from the actual typed datum"
            )
