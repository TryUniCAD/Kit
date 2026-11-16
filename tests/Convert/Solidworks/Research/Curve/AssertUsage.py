from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.AssertSnapshot import AssertSnapshot


# load and store need independent provenance rather than a registry wide confidence claim
def AssertUsage(UsageData: dict[str, object]) -> None:
    for Direction in ("load", "store"):
        AssertSnapshot(CastValue(dict[str, object], UsageData[Direction]))
