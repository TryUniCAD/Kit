from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# rigid placement applies the authored row basis and translation in native arithmetic order without recomputing the independent local sphere
def PlacePoint(
    FrameValue: PlaneFrame, PointValue: tuple[float, float, float]
) -> tuple[float, float, float]:
    First, Second, Third = PointValue
    NumbersValue = tuple(
        Origin + First * AxisU + Second * AxisV + Third * Normal
        for Origin, AxisU, AxisV, Normal in zip(
            FrameValue.OriginValue,
            FrameValue.AxisU,
            FrameValue.AxisV,
            FrameValue.NormalValue,
            strict=True,
        )
    )
    return NumbersValue[0], NumbersValue[1], NumbersValue[2]
