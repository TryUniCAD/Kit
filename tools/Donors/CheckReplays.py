from __future__ import annotations

import argparse as Argparse
import sys as System
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.Donors.CompareCounts import CompareCounts
from tools.Donors.ReplayBaseline import FormatCounts, LoadCounts
from tools.Donors.ReplayCount import ReplayCount
from tools.Donors.ReplayRules import KFieldRule, KStandardPath
from tools.Donors.ScanCounts import ScanCounts


def ParseArgs(ArgValues: Sequence[str] | None = None) -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="keep recorded payload debt in production writers from growing"
    )
    _ = ParserInfo.add_argument("--baseline-file", type=FilePath, required=True)
    _ = ParserInfo.add_argument(
        "--update-baseline",
        action="store_true",
        help="lower the baseline to the current counts when nothing grew",
    )
    _ = ParserInfo.add_argument("PathValues", metavar="PATH", nargs="+")
    return ParserInfo.parse_args(ArgValues)


def ReportCounts(
    CurrentList: Sequence[ReplayCount], GrowthList: list[str], StaleList: list[str]
) -> int:
    for ProblemText in (*GrowthList, *StaleList):
        print(ProblemText)
    if GrowthList:
        print(
            f"recorded payload debt grew in {len(GrowthList)} places; see {KStandardPath}",
            file=System.stderr,
        )
        return 1
    if StaleList:
        print(
            "recorded payload debt fell; rerun with --update-baseline and commit it",
            file=System.stderr,
        )
        return 1
    FieldTotal = sum(
        CountItem.CountValue
        for CountItem in CurrentList
        if CountItem.RuleCode == KFieldRule
    )
    RootTotal = len({CountItem.RootPath for CountItem in CurrentList})
    SummaryText = f"{FieldTotal} recorded field operations remain in {RootTotal} roots"
    print(f"recorded payload ratchet passed: {SummaryText}")
    return 0


def MainRun(ArgValues: Sequence[str] | None = None) -> int:
    NamespaceInfo = ParseArgs(ArgValues)
    BaselinePath: FilePath = NamespaceInfo.baseline_file
    try:
        CurrentList = ScanCounts(NamespaceInfo.PathValues)
        BaselineMap = LoadCounts(BaselinePath)
    except (OSError, SyntaxError, UnicodeError, ValueError) as ErrorInfo:
        print(f"recorded payload ratchet input error: {ErrorInfo}", file=System.stderr)
        return 2
    GrowthList, StaleList = CompareCounts(CurrentList, BaselineMap)
    if NamespaceInfo.update_baseline and not GrowthList:
        _ = BaselinePath.write_text(FormatCounts(CurrentList), encoding="utf-8")
        StaleList = []
    return ReportCounts(CurrentList, GrowthList, StaleList)


if __name__ == "__main__":
    raise SystemExit(MainRun())
