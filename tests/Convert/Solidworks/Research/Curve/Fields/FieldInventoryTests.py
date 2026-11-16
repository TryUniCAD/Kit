from __future__ import annotations

from json import dumps as DumpJson
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from pytest import mark as MarkTests
from tests.Convert.Solidworks.Research.Curve.AssertFixtures import AssertFixtures
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus
from tests.Convert.Solidworks.Research.Curve.ReadManifest import ReadManifest
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Curve.Fields.AssertInventory import (
    AssertInventory,
)
from tests.Convert.Solidworks.Research.Curve.Fields.InventoryCases import (
    KInventoryCases,
)
from tests.Convert.Solidworks.Research.Curve.Fields.RunFieldCli import RunFieldCli


# actual native corpus inputs must produce complete inventories through fresh command processes
@MarkTests.parametrize(("StreamName", "IsLinked"), KInventoryCases)
def TestFieldScan(TmpPath: FilePath, StreamName: str, IsLinked: bool) -> None:
    Entries = AssertFixtures(ReadManifest())
    OutputDir = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath))
        / "SourceParser/Curve/Fields"
    )
    OutputDir.mkdir(parents=True, exist_ok=True)
    Prefix = "Linked" if IsLinked else "Primary"
    LeafName = StreamName.rsplit("/", 1)[-1].replace("-", "")
    ReportPath = OutputDir / f"{Prefix}{LeafName}.json"
    Outcome = RunFieldCli(
        str(KCurveCorpus / "*.SLDPRT"), StreamName, ReportPath, IsLinked
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Statistics = AssertInventory(ReadObject(ReportPath), Entries, StreamName, IsLinked)
    CheckPath = ReportPath.with_suffix(".checked.json")
    _ = CheckPath.write_text(
        DumpJson(
            {
                "scope": "decoded source field inventory contract only",
                "is_writer_output": False,
                "native_acceptance_inherited": False,
                "stream": StreamName,
                "linked_configurations": IsLinked,
                "file_count": len(Statistics),
                "value_kind_counts": Statistics,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
