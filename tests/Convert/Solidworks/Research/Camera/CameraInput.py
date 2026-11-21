from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleBodyInput import (
    MakeCircleBody,
)


# discovery camera requests reuse neutral body inputs without exposing the independent sealed sources
def MakeCamera(ViewIndex: int) -> dict[str, object]:
    Request = MakeCircleBody(
        [0.003917, -0.005139],
        0.011173,
        0.007713,
        "CameraDiscovery",
        "diameter",
        [0.0229111, 0.0093859, 0.0],
    )
    Presentation = CastValue(dict[str, object], Request["presentation"])
    Presentation["initial_view"] = {
        "named_view": ViewIndex,
        "translation": [0.003173, -0.007191, 0.005713],
        "scale2": 37.173,
    }
    return Request
