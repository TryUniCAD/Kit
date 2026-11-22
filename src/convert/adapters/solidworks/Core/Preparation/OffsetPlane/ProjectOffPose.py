from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetFrame import (
    OffsetFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# validate the projected pose using the reader scaling before supplying the writer millimetre pose
def ProjectOffPose(
    BasePlane: SupportPlane, Carrier: SupportPlane, SignedValue: float
) -> SupportPlane:
    BaseFrame = OffBaseFrame(ReadPrincAxis(BasePlane.transform))
    FrameValue = OffsetFrame(BaseFrame, SignedValue)
    if Carrier.transform != Transform(
        SpaceVector(*(Coord * 1000.0 for Coord in FrameValue.OriginValue)),
        SpaceVector(*FrameValue.AxisU),
        SpaceVector(*FrameValue.AxisV),
        SpaceVector(*FrameValue.NormalValue),
    ):
        raise ValueError("SOLIDWORKS offset readback pose disagrees with its signed D1")
    PoseValue = OffsetFrame(BaseFrame, SignedValue / 0.001)
    return ReplaceValue(
        Carrier,
        transform=ReplaceValue(
            Carrier.transform, origin=SpaceVector(*PoseValue.OriginValue)
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
