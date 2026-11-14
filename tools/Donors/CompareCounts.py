from __future__ import annotations

from collections.abc import Mapping, Sequence

from tools.Donors.ReplayCount import ReplayCount
from tools.Donors.ReplayRules import KRuleNames


def CompareCounts(
    CurrentList: Sequence[ReplayCount],
    BaselineMap: Mapping[tuple[str, str], int],
) -> tuple[list[str], list[str]]:
    GrowthList: list[str] = []
    StaleList: list[str] = []
    CurrentMap = {
        (CountItem.RootPath, CountItem.RuleCode): CountItem.CountValue
        for CountItem in CurrentList
    }
    for KeyPair, CountValue in sorted(CurrentMap.items()):
        RootText, RuleCode = KeyPair
        LabelText = f"{RootText}: {RuleCode} {KRuleNames[RuleCode]}"
        Allowed = BaselineMap.get(KeyPair)
        if Allowed is None:
            GrowthList.append(
                f"{LabelText} are new ({CountValue}); generate them instead"
            )
        elif CountValue > Allowed:
            GrowthList.append(f"{LabelText} grew from {Allowed} to {CountValue}")
        elif CountValue < Allowed:
            StaleList.append(f"{LabelText} fell from {Allowed} to {CountValue}")
    for KeyPair, Allowed in sorted(BaselineMap.items()):
        if KeyPair not in CurrentMap:
            RootText, RuleCode = KeyPair
            StaleList.append(
                f"{RootText}: {RuleCode} {KRuleNames[RuleCode]} fell from {Allowed} to 0"
            )
    return GrowthList, StaleList
