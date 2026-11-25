from hashlib import file_digest as FileDigest
from json import loads as LoadJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# the audit must retain the strict source graph while partial provenance accounts for native stream bytes
def VerifyLayerPins(RunPath: FilePath, SourceSha: str) -> None:
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    Strict = LoadJson((RunPath / "Input-strict.json").read_bytes())["document"]
    Partial = LoadJson((RunPath / "Input-partial.json").read_bytes())["document"]
    assert Audit["source_sha256"] == SourceSha
    assert Strict["source"]["sha256"] == Partial["source"]["sha256"] == SourceSha
    assert (Audit["feature_layer"], Audit["provenance_layer"]) == ("strict", "partial")
    Attempts = Audit["reader_attempts"]
    assert Attempts["strict"] == Attempts["partial"] == {"status": "decoded"}
    assert Audit["diagnostics"] == Strict["diagnostics"]["$tuple"]
    (CutStep,) = (
        StepValue
        for StepValue in Strict["feature_timeline"]["$tuple"]
        if (StepValue.get("definition") or {}).get("$type") == "DistanceCut"
    )
    assert CutStep["id"] == "fusion:0:322"
    assert CutStep["id"] in {
        StepValue["id"] for StepValue in Audit["features_without_experiment"]
    }
    Members = LoadJson((RunPath / "Input-container.json").read_bytes())["members"]
    Unattributed = sum(
        EndPos - StartPos for _, StartPos, EndPos in Audit["unattributed_stream_ranges"]
    )
    assert sum(Member["size"] for Member in Members) - Unattributed == 11067
    assert Audit["unattributed_stream_ranges"] and Audit["whole_file_verified"] is False
    Outcome = LoadJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Outcome["status"] == "coverage_incomplete"


# a real saved corner cut exposes the missing strict provenance through the same command researchers use
def CheckLayerScope(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    CapturePath = RootPath / "re/Fusion/Reconstruction/BoundaryCuts"
    SourcePath = CapturePath / "Controls/RequestedCorner.f3d"
    SourceSha = LoadJson((CapturePath / "RequestedCorner.json").read_bytes())["sha256"]
    with SourcePath.open("rb") as Stream:
        assert FileDigest(Stream, "sha256").hexdigest() == SourceSha
    RunPath = TmpPath / "CornerScope"
    Result = RunProcess(
        (
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ),
        cwd=TmpPath,
        env={**KEnvironment, "KIT_NATIVE_API_DIRECTORY": str(TmpPath / "NativeApi")},
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stdout + Result.stderr
    VerifyLayerPins(RunPath, SourceSha)
