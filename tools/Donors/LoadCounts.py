from __future__ import annotations

from pathlib import Path as FilePath

from tools.Donors.ReplayRules import KRuleNames


def LoadCounts(BaselinePath: FilePath) -> dict[tuple[str, str], int]:
    CountMap: dict[tuple[str, str], int] = {}
    for LineText in BaselinePath.read_text(encoding="utf-8").splitlines():
        if not LineText or LineText.startswith("#"):
            continue
        RootText, RuleCode, CountText = LineText.split("\t")
        if RuleCode not in KRuleNames:
            raise ValueError(f"unknown baseline rule: {RuleCode}")
        KeyPair = (RootText, RuleCode)
        if KeyPair in CountMap:
            raise ValueError(f"duplicate baseline entry: {RootText} {RuleCode}")
        CountMap[KeyPair] = int(CountText)
    return CountMap
