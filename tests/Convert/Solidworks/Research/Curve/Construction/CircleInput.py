from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# explicit circle geometry drives the first isolated sketch synthesis rung without native files
def MakeCircleInput(
    CenterValue: list[float], RadiusValue: float, NameValue: str, PlaneValue: str
) -> dict[str, object]:
    Request = MakePartInput([], 0.0, NameValue)
    Document = CastValue(dict[str, object], Request["document"])
    del Document["vertices_m"]
    del Document["depth_m"]
    Document.update(
        profile_kind="circle",
        feature_kind="sketch",
        center_m=CenterValue,
        radius_m=RadiusValue,
        plane_axis=PlaneValue,
    )
    return Request
