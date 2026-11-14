from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath

from tools.Donors.CountSource import CountSource
from tools.Donors.FindRoot import FindRoot
from tools.Donors.ListSources import ListSources
from tools.Donors.ReplayRules import KFieldRule, KReplayRule
from tools.Donors.ShowPath import ShowPath


def ScanCounts(PathValues: Sequence[str]) -> dict[tuple[str, str], int]:
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
    return CountMap
