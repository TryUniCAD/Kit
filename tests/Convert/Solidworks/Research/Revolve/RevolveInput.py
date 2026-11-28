from __future__ import annotations

from math import radians as Radians
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# synthetic profile and axis parameters let the process prove origin and sweep changes
def MakeRevolve(
    Plane: str, PartName: str, Degrees: float, Reverse: bool
) -> dict[str, object]:
    Request = MakePartInput(
        [[0.01, -0.02], [0.035, -0.02], [0.035, 0.031], [0.01, 0.031]], 0.012, PartName
    )
    Document = CastValue(dict[str, object], Request["document"])
    del Document["depth_m"], Document["extrusion_name"]
    Document.update(
        feature_kind="revolve",
        plane_axis=Plane,
        revolution_name=PartName + " revolve",
        axis_start_m=[-0.006, -0.033],
        axis_end_m=[-0.006, 0.041],
        angle_rad=Radians(Degrees),
        reverse_direction=Reverse,
    )
    return Request
