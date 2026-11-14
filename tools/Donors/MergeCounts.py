from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath

from tools.Donors.IsCovered import IsCovered


def MergeCounts(
    CurrentMap: Mapping[tuple[str, str], int],
    BaselineMap: Mapping[tuple[str, str], int],
    ScopeList: Sequence[PurePosixPath],
) -> dict[tuple[str, str], int]:
    MergedMap = {
        KeyPair: CountValue
        for KeyPair, CountValue in BaselineMap.items()
        if not IsCovered(KeyPair[0], ScopeList)
    }
    MergedMap.update(
        (KeyPair, CountValue)
        for KeyPair, CountValue in CurrentMap.items()
        if IsCovered(KeyPair[0], ScopeList)
    )
    return MergedMap
