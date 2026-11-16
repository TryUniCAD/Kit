from __future__ import annotations

from os import getenv as ReadEnv
from pathlib import Path as FilePath
from pytest import mark as MarkTests
from tests.convert.solidworks.research.ArchiveProcess import RunArchive
from tests.convert.solidworks.research.Curve.CorpusPaths import (
    KCurveCorpus,
    KPrimaryStreams,
)
from tests.convert.solidworks.research.Curve.ReadManifest import ReadManifest
from tests.convert.solidworks.research.Curve.AssertFixtures import AssertFixtures
from tests.convert.solidworks.research.Curve.SaveReceipt import SaveReceipt
from tests.convert.solidworks.research.Curve.ReadObject import ReadObject
from tests.convert.solidworks.research.Curve.AssertReport import AssertReport


# independent interpreters must preserve every selected native stream without relying on tentative schema coverage
@MarkTests.parametrize("IsLinked", (False, True))
def TestCurveRound(TmpPath: FilePath, IsLinked: bool) -> None:
    Entries = AssertFixtures(ReadManifest())
    Selected = ("Contents/Config-0-ResolvedFeatures",) if IsLinked else KPrimaryStreams
    OutputDir = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath)) / "SourceParser" / "Curve"
    )
    OutputDir.mkdir(parents=True, exist_ok=True)
    ReportPath = OutputDir / (
        "LinkedConfig.json" if IsLinked else "PrimaryStreams.json"
    )
    ExtraArgs: tuple[str, ...] = ("--require-proven", "--report", str(ReportPath))
    if IsLinked:
        ExtraArgs += ("--link-config",)
    Outcome = RunArchive(str(KCurveCorpus / "*.SLDPRT"), ",".join(Selected), ExtraArgs)
    SaveReceipt(ReportPath, Outcome, IsLinked)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    AssertReport(ReadObject(ReportPath), Entries, Selected, IsLinked)
