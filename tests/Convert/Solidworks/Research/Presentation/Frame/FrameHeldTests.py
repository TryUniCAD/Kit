from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Frozen.FrozenRoot import FrozenRoot
from tests.Convert.Solidworks.Research.Presentation.Frame.CheckFrameOut import (
    CheckFrameOut,
)
from tests.Convert.Solidworks.Research.Presentation.Frame.ReadFrameCase import (
    ReadFrameCase,
)


# untouched native sources need complete predictions from the already published corrected writer
def TestFrameHold() -> None:
    Inventory, Cases = ReadFrameCase()
    with FrozenRoot(Inventory) as SourceRoot:
        for CaseValue in Cases:
            CheckFrameOut(
                CaseValue, SourceRoot, CastValue(str, Inventory["source_revision"])
            )
