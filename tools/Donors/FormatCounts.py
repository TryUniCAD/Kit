from __future__ import annotations

from collections.abc import Mapping

from tools.Donors.ReplayRules import KStandardPath

KBaselineHeader = (
    "# recorded payload debt in production writers, one root per line",
    "# columns are root, rule and the largest permitted count",
    "# counts may only fall; lower them with --update-baseline",
    f"# see {KStandardPath}",
)


def FormatCounts(CountMap: Mapping[tuple[str, str], int]) -> str:
    RowList = [
        f"{RootText}\t{RuleCode}\t{CountValue}"
        for (RootText, RuleCode), CountValue in sorted(CountMap.items())
    ]
    return "\n".join((*KBaselineHeader, *RowList)) + "\n"
