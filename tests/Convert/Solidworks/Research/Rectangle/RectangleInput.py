from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# neutral requests keep text anchors independent of the serialized dimension records
def MakeRectInput(
    NameValue: str,
    Vertices: list[list[float]],
    DepthValue: float,
    TextAnchors: list[list[float]],
    RouteCenterline: bool,
) -> dict[str, object]:
    Request = MakePartInput(Vertices, DepthValue, NameValue)
    Document = CastValue(dict[str, object], Request["document"])
    Document["configuration_name"] = "Default"
    Document["rectangle_dimensions"] = {
        "width_text_m": TextAnchors[0],
        "height_text_m": TextAnchors[1],
        "route_centerline": RouteCenterline,
    }
    return Request
