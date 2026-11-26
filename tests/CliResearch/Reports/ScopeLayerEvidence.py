from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.CliResearch.Reports.ScopeRangeEvidence import VerifyFileGaps


# the audit must retain the strict source graph while partial provenance accounts for native stream bytes
def VerifyLayerPins(RunPath: FilePath, SourcePath: FilePath, SourceSha: str) -> None:
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    Strict = LoadJson((RunPath / "Input-strict.json").read_bytes())["document"]
    PartialPath = RunPath / "Input-partial.json"
    Partial = LoadJson(PartialPath.read_bytes())["document"]
    assert Audit["source_sha256"] == SourceSha
    assert Strict["source"]["sha256"] == Partial["source"]["sha256"] == SourceSha
    assert (Audit["feature_layer"], Audit["provenance_layer"]) == ("strict", "partial")
    Attempts = Audit["reader_attempts"]
    assert Attempts["strict"] == Attempts["partial"] == {"status": "decoded"}
    assert Audit["diagnostics"] == Strict["diagnostics"]["$tuple"]
    (CutStep,) = (
        StepValue
        for StepValue in Strict["feature_timeline"]["$tuple"]
        if StepValue["definition"] is not None
        and StepValue["definition"]["$type"] == "DistanceCut"
    )
    assert CutStep["id"] == "fusion:0:322"
    assert CutStep["id"] in {
        StepValue["id"] for StepValue in Audit["features_without_experiment"]
    }
    Members = LoadJson((RunPath / "Input-container.json").read_bytes())["members"]
    VerifyFileGaps(
        SourcePath,
        PartialPath,
        [(Member["name"], Member["size"]) for Member in Members],
        Audit["unattributed_stream_ranges"],
    )
    assert Audit["unattributed_stream_ranges"] and Audit["whole_file_verified"] is False
    Outcome = LoadJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Outcome["status"] == "coverage_incomplete"
