from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# selected sketch points require the actual support frame before becoming neutral model coordinates
def MapRevPoint(
    FrameValue: Transform, PositionValue: tuple[float, float]
) -> SpaceVector:
    AlongValue, AcrossValue = PositionValue
    return SpaceVector(
        FrameValue.origin.x
        + FrameValue.x_axis.x * AlongValue
        + FrameValue.y_axis.x * AcrossValue,
        FrameValue.origin.y
        + FrameValue.x_axis.y * AlongValue
        + FrameValue.y_axis.y * AcrossValue,
        FrameValue.origin.z
        + FrameValue.x_axis.z * AlongValue
        + FrameValue.y_axis.z * AcrossValue,
    )
