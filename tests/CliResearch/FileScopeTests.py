from hashlib import file_digest as FileDigest
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


# a renamed real input must retain its byte identity and select experiments from its decoded features
def CheckFileScope(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    SourcePath = (
        RootPath
        / "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/P04-fusion-termination-through-all.f3d"
    )
    InputPath = TmpPath / "unknown.bin"
    _ = InputPath.write_bytes(SourcePath.read_bytes())
    RunPath = TmpPath / "run"
    Result = RunProcess(
        [
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(InputPath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stderr
    Audit = LoadJson((RunPath / "FileScope.json").read_bytes())
    with InputPath.open("rb") as Stream:
        assert Audit["source_sha256"] == FileDigest(Stream, "sha256").hexdigest()
    assert Audit["member_count"] > 0 and Audit["unattributed_stream_ranges"]
    assert "family:extrude:cut-extrude" in Audit["selected_experiments"]
    Brep = Audit["native_classes"]["classes"]["5662F619-2281-4AD9-93DC-1FCFDA1062E7"]
    assert Brep["metatypes"] == ["BrepRefMetaType"] and "rRecipe" in Brep["fields"]
    assert (
        "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
        not in Audit["reader_attempts"]["strict"]["message"]
    )
    assert Audit["whole_file_verified"] is False
    Outcome = LoadJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Outcome["status"] == "coverage_incomplete"
    assert Outcome["scopes"]["p04-through-all-body-selection"]["assessment_job"]
