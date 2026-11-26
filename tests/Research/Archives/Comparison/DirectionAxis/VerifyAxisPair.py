from pathlib import Path as FilePath
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.DirectionAxis.GenerateAxis import GenerateAxis
from tests.Research.Archives.Comparison.DirectionAxis.VerifyAxis import VerifyAxis
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)


# each reported source must bind to its own independently decoded native identities
def VerifyAxisPair(TmpPath: FilePath, Archived: CadDocument) -> None:
    Generated = GenerateAxis(TmpPath)
    assert Archived.source.sha256 != Generated.source.sha256
    (Selection,) = Generated.selections
    Provenance = Selection.provenance
    assert Provenance is not None
    (SpanValue,) = Provenance.spans
    assert (SpanValue.offset, SpanValue.length) == (12036, 3025)
    assert Selection.id == "sldprt:selection:71:axis:57:N_Axis"
    Report = ReadReport(
        RunComparison(WriteInputs(TmpPath, Archived, Generated)), "different", 2
    )
    Sources = CastValue(dict[str, dict[str, object]], Report["sources"])
    VerifyAxis(Sources["left"], Archived.source.sha256, True)
    VerifyAxis(
        Sources["right"],
        Generated.source.sha256,
        True,
        (71, 57, SpanValue.offset, SpanValue.length),
    )
