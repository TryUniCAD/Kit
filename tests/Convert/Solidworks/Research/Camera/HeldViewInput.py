from __future__ import annotations

from copy import deepcopy as CopyValue
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.HeldoutInput import (
    MakeHeldBody,
)


# unseen view predictions must use only public semantic specifications without opening native source data
def MakeHeldView(CaseValue: dict[str, object]) -> dict[str, object]:
    Request = MakeHeldBody(CaseValue)
    Presentation = CastValue(dict[str, object], Request["presentation"])
    Presentation["initial_view"] = CopyValue(CaseValue["view_request"])
    return Request
