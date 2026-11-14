from __future__ import annotations

import sys as System
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.Donors.FindGrowth import FindGrowth
from tools.Donors.FindScope import FindScope
from tools.Donors.FindStale import FindStale
from tools.Donors.FormatCounts import FormatCounts
from tools.Donors.LoadCounts import LoadCounts
from tools.Donors.MergeCounts import MergeCounts
from tools.Donors.ParseArgs import ParseArgs
from tools.Donors.ReportCounts import ReportCounts
from tools.Donors.ScanCounts import ScanCounts


def MainRun(ArgValues: Sequence[str] | None = None) -> int:
    NamespaceInfo = ParseArgs(ArgValues)
    BaselinePath: FilePath = NamespaceInfo.baseline_file
    PathValues: list[str] = NamespaceInfo.PathValues
    try:
        CurrentMap = ScanCounts(PathValues)
        BaselineMap = LoadCounts(BaselinePath)
    except (OSError, SyntaxError, UnicodeError, ValueError) as ErrorInfo:
        print(f"recorded payload ratchet input error: {ErrorInfo}", file=System.stderr)
        return 2
    ScopeList = FindScope(PathValues)
    GrowthList = FindGrowth(CurrentMap, BaselineMap)
    StaleList = FindStale(CurrentMap, BaselineMap, ScopeList)
    if NamespaceInfo.update_baseline and not GrowthList:
        MergedMap = MergeCounts(CurrentMap, BaselineMap, ScopeList)
        _ = BaselinePath.write_text(FormatCounts(MergedMap), encoding="utf-8")
        StaleList = []
    return ReportCounts(CurrentMap, GrowthList, StaleList)


if __name__ == "__main__":
    raise SystemExit(MainRun())
