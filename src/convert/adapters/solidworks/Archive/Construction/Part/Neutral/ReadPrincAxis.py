from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# matching the complete model basis preserves the actual support orientation and excludes translated or arbitrary frames
def ReadPrincAxis(TransformValue: Transform) -> str:
    for AxisValue in ("z", "x", "y"):
        FrameValue = PrincipalFrame(AxisValue)
        Expected = Transform(
            SpaceVector(*FrameValue.OriginValue),
            SpaceVector(*FrameValue.AxisU),
            SpaceVector(*FrameValue.AxisV),
            SpaceVector(*FrameValue.NormalValue),
        )
        if TransformValue == Expected:
            return AxisValue
    raise ValueError("boss support must be a canonical principal frame at origin")
