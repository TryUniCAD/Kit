from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.Comparison.DirectionAxis.AlterAxis import AlterAxis
from tests.Research.Archives.Comparison.DirectionAxis.AxisIssues import AxisIssues
from tests.Research.Archives.Comparison.DirectionAxis.CaptureAxis import CaptureAxis
from tests.Research.Archives.Comparison.DirectionAxis.VerifyAxis import VerifyAxis
from tests.Research.Archives.Comparison.DirectionAxis.VerifyAxisPair import (
    VerifyAxisPair,
)
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)


# each wrong direction owner must withhold only the additive reader observation
def CheckDirection(TmpPath: FilePath) -> None:
    Document = CaptureAxis(TmpPath)
    SourceHash = Document.source.sha256
    Control = ReadReport(
        RunComparison(WriteInputs(TmpPath, Document, Document)), "different", 2
    )
    Baseline = CastValue(dict[str, dict[str, object]], Control["sources"])
    VerifyAxis(Baseline["left"], SourceHash, True)
    VerifyAxis(Baseline["right"], SourceHash, True)
    Issues = AxisIssues(Baseline["left"])
    assert AxisIssues(Baseline["right"]) == Issues
    VerifyAxisPair(TmpPath, Document)
    for FaultName in ("owner", "target", "normal", "provenance"):
        Changed = AlterAxis(Document, FaultName)
        Report = ReadReport(
            RunComparison(WriteInputs(TmpPath, Document, Changed)), "different", 2
        )
        Sources = CastValue(dict[str, dict[str, object]], Report["sources"])
        assert Sources["left"] == Baseline["left"], FaultName
        VerifyAxis(Sources["right"], SourceHash, False)
        assert AxisIssues(Sources["right"]) == Issues, FaultName
