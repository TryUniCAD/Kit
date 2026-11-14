from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath

from tools.Donors.CountSource import CountSource
from tools.Donors.FindRoot import FindRoot
from tools.Donors.ListSources import ListSources, ShowPath
from tools.Donors.ReplayCount import ReplayCount
from tools.Donors.ReplayRules import KFieldRule, KReplayRule


def ScanCounts(PathValues: Sequence[str]) -> list[ReplayCount]:
    CountMap: dict[tuple[str, str], int] = {}
    for SourcePath in ListSources(PathValues):
        SourceText = SourcePath.read_text(encoding="utf-8")
        FieldTotal, CallTotal = CountSource(SourceText, str(SourcePath))
        RootText = FindRoot(PurePosixPath(ShowPath(SourcePath)))
        for RuleCode, CountValue in (
            (KFieldRule, FieldTotal),
            (KReplayRule, CallTotal),
        ):
            if CountValue:
                KeyPair = (RootText, RuleCode)
                CountMap[KeyPair] = CountMap.get(KeyPair, 0) + CountValue
    return sorted(
        ReplayCount(KeyPair[0], KeyPair[1], CountValue)
        for KeyPair, CountValue in CountMap.items()
    )
