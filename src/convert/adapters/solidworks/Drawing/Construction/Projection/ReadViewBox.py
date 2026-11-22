from itertools import product as Cartesian

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.MakeViewBox import (
    MakeViewBox,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)


# the measured view profile must use a real generated axis aligned rectangular child rather than infer shape from cached bounds
def ReadViewBox(ChildValue: PartCandidate) -> dict[str, float]:
    if type(ChildValue) is not PartCandidate:
        raise TypeError(
            "drawing projection requires an actual generated part candidate"
        )
    PlanValue, ProfileValue = ChildValue.PlanValue, ChildValue.ProfileValue
    FrameValue = ProfileValue.FrameValue
    PointsValue = tuple(
        (
            NeedDrawNumber(NeedConceptMap(Point.FieldsValue["pos"])["x"]),
            NeedDrawNumber(NeedConceptMap(Point.FieldsValue["pos"])["y"]),
        )
        for Point in ProfileValue.GeometryValue.PointValues
    )
    if (
        isinstance(PlanValue, CirclePlan)
        or PointsValue != PlanValue.VerticesValue
        or len(PointsValue) != 4
        or len(ProfileValue.GeometryValue.LineValues) != 4
    ):
        raise ValueError(
            "drawing projection requires the actual four line child profile"
        )
    if (
        FrameValue.AxisU,
        FrameValue.AxisV,
        FrameValue.OriginValue,
        FrameValue.NormalValue,
    ) != (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 0),
        (0, 0, 1),
    ):
        raise ValueError("drawing projection requires the qualified child xy frame")
    LowValue = (
        min(Point[0] for Point in PointsValue),
        min(Point[1] for Point in PointsValue),
        0.0,
    )
    HighValue = (
        max(Point[0] for Point in PointsValue),
        max(Point[1] for Point in PointsValue),
        NeedDrawNumber(PlanValue.DepthValue),
    )
    Perimeter = zip(PointsValue, (*PointsValue[1:], PointsValue[0]), strict=True)
    if (
        HighValue[2] <= 0
        or set(PointsValue)
        != set(Cartesian(*zip(LowValue[:2], HighValue[:2], strict=True)))
        or not all(
            (LeftValue[0] == RightValue[0]) != (LeftValue[1] == RightValue[1])
            for LeftValue, RightValue in Perimeter
        )
    ):
        raise ValueError("drawing projection requires an xy aligned rectangular prism")
    return MakeViewBox(LowValue, HighValue)
