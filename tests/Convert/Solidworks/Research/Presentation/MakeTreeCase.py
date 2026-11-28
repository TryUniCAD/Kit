from __future__ import annotations

from tests.Convert.Solidworks.Research.Camera.MakeViewCase import MakeViewCase
from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput


# public locked specifications must compose through the same neutral input path before private reference access
def MakeTreeCase(CaseValue: dict[str, object]) -> dict[str, object]:
    return MakeTreeInput(MakeViewCase(CaseValue))
