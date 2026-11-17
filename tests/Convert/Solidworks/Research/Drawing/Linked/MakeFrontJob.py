from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Definition.MakeDefInput import (
    MakeDefInput,
)
from tests.Convert.Solidworks.Research.Drawing.MakeFrontInput import MakeFrontInput


# independently authored child dimensions and drawing identities must exercise complete linked emission without saved inputs
def MakeFrontJob(
    Label: str, Width: float, Height: float, Depth: float
) -> dict[str, object]:
    Request = MakeFrontInput(Label, Width, Height, Depth)
    Request["drawing"] = MakeDefInput(Label, 11, 3)
    ViewValue = CastValue(dict[str, object], Request["view"])
    ViewValue["name"] = Label + " front"
    ViewValue["supports"] = {
        "detail": Label + " details",
        "sheet_plane": Label + " sheet plane",
        "sheet_profile": Label + " sheet profile",
        "model_plane": Label + " model plane",
        "model_profile": Label + " model profile",
    }
    return {"schema": "kit.sw2026.sdk-front-definition-process.v1", "request": Request}
