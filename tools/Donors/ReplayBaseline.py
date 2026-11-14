from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.Donors.ReplayCount import ReplayCount
from tools.Donors.ReplayRules import KStandardPath

KBaselineHeader = (
    "# recorded payload debt in production writers, one root per line",
    "# columns are root, rule and the largest permitted count",
    "# counts may only fall; lower them with --update-baseline",
    f"# see {KStandardPath}",
)


def LoadCounts(BaselinePath: FilePath) -> dict[tuple[str, str], int]:
    CountMap: dict[tuple[str, str], int] = {}
    for LineText in BaselinePath.read_text(encoding="utf-8").splitlines():
        if not LineText or LineText.startswith("#"):
            continue
        RootText, RuleCode, CountText = LineText.split("\t")
        KeyPair = (RootText, RuleCode)
        if KeyPair in CountMap:
            raise ValueError(f"duplicate baseline entry: {RootText} {RuleCode}")
        CountMap[KeyPair] = int(CountText)
    return CountMap


def FormatCounts(CountList: Sequence[ReplayCount]) -> str:
    RowList = [
        f"{CountItem.RootPath}\t{CountItem.RuleCode}\t{CountItem.CountValue}"
        for CountItem in sorted(CountList)
    ]
    return "\n".join((*KBaselineHeader, *RowList)) + "\n"
