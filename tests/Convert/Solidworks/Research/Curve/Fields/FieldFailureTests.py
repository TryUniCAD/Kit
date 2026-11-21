from __future__ import annotations

from os import getenv as ReadEnv
from pathlib import Path as FilePath
from pytest import mark as MarkTests
from tests.Convert.Solidworks.Research.Curve.AssertFixtures import AssertFixtures
from tests.Convert.Solidworks.Research.Curve.ReadManifest import ReadManifest
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Curve.Fields.AssertFailure import AssertFailure
from tests.Convert.Solidworks.Research.Curve.Fields.PrepareFailure import PrepareFailure
from tests.Convert.Solidworks.Research.Curve.Fields.RunFieldCli import RunFieldCli


# incomplete real inputs must retain explicit failures instead of successful empty field graphs
@MarkTests.parametrize(
    "FailureKind", ("EmptyPattern", "MissingStream", "TruncatedFixture")
)
def TestFieldFail(TmpPath: FilePath, FailureKind: str) -> None:
    Entries = AssertFixtures(ReadManifest())
    Pattern, StreamName, Expected = PrepareFailure(TmpPath, FailureKind, Entries)
    OutputDir = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath))
        / "SourceParser/Curve/Fields/Failures"
    )
    OutputDir.mkdir(parents=True, exist_ok=True)
    ReportPath = OutputDir / f"{FailureKind}.json"
    Outcome = RunFieldCli(Pattern, StreamName, ReportPath, False)
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    AssertFailure(ReadObject(ReportPath), Expected, Pattern, StreamName, FailureKind)
