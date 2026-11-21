from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Linked.MakeFrontJob import MakeFrontJob


# new named requests must preserve neutral child binding while independently varying their authored view family and scale
def MakeNamedJob(
    Label: str,
    Orientation: str,
    ScaleValue: float,
    Width: float,
    Height: float,
    Depth: float,
    PositionX: float,
    PositionY: float,
) -> dict[str, object]:
    JobValue = MakeFrontJob(Label, Width, Height, Depth)
    JobValue["schema"] = "kit.sw2026.sdk-named-definition-process.v1"
    JobValue["orientation"] = Orientation
    Request = CastValue(dict[str, object], JobValue["request"])
    ViewValue = CastValue(dict[str, object], Request["view"])
    ViewValue.update(
        orientation=Orientation, scale=ScaleValue, position=[PositionX, PositionY]
    )
    return JobValue
