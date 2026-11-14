from __future__ import annotations

import sys as System
from collections.abc import Mapping, Sequence

from tools.Donors.ReplayRules import KFieldRule, KStandardPath


def ReportCounts(
    CurrentMap: Mapping[tuple[str, str], int],
    GrowthList: Sequence[str],
    StaleList: Sequence[str],
) -> int:
    for ProblemText in (*GrowthList, *StaleList):
        print(ProblemText)
    if GrowthList:
        CountText = f"recorded payload debt grew in {len(GrowthList)} places"
        print(f"{CountText}; see {KStandardPath}", file=System.stderr)
        return 1
    if StaleList:
        print(
            "recorded payload debt fell; rerun with --update-baseline and commit it",
            file=System.stderr,
        )
        return 1
    FieldTotal = sum(
        CountValue
        for (_, RuleCode), CountValue in CurrentMap.items()
        if RuleCode == KFieldRule
    )
    RootTotal = len({RootText for RootText, _ in CurrentMap})
    SummaryText = f"{FieldTotal} recorded field operations remain in {RootTotal} roots"
    print(f"recorded payload ratchet passed: {SummaryText}")
    return 0
