from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath

from tools.Donors.FormatLabel import FormatLabel
from tools.Donors.IsCovered import IsCovered


def FindStale(
    CurrentMap: Mapping[tuple[str, str], int],
    BaselineMap: Mapping[tuple[str, str], int],
    ScopeList: Sequence[PurePosixPath],
) -> list[str]:
    StaleList: list[str] = []
    for KeyPair, Allowed in sorted(BaselineMap.items()):
        CountValue = CurrentMap.get(KeyPair, 0)
        if CountValue < Allowed and IsCovered(KeyPair[0], ScopeList):
            LabelText = FormatLabel(KeyPair)
            StaleList.append(f"{LabelText} fell from {Allowed} to {CountValue}")
    return StaleList
