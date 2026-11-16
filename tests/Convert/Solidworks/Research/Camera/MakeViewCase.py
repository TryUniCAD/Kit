from __future__ import annotations

from tests.Convert.Solidworks.Research.Camera.HeldViewInput import MakeHeldView


# native radial terminology must map to the existing radius input without changing locked writer dependencies
def MakeViewCase(CaseValue: dict[str, object]) -> dict[str, object]:
    CaseInput = dict(CaseValue)
    if CaseInput["dimension_kind"] == "radial":
        CaseInput["dimension_kind"] = "radius"
    return MakeHeldView(CaseInput)
