from __future__ import annotations

from tools.Donors.ReplayRules import KRuleNames


def FormatLabel(KeyPair: tuple[str, str]) -> str:
    RootText, RuleCode = KeyPair
    return f"{RootText}: {RuleCode} {KRuleNames[RuleCode]}"
