from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.CliResearch.RimFillets.CaseNames import KCaseNames


# real native archives must retain their complete typed model across a fresh reader writer process
@TestMark.parametrize(
    "CaseName",
    KCaseNames
    + tuple("depth-" + Value for Value in KCaseNames if Value.startswith("holdout-"))
    + ("fresh-01", "fresh-02", "fresh-03", "fresh-04"),
)
def CheckRimCycle(TmpPath: FilePath, CaseName: str) -> None:
    RootPath = ResearchRoot()
    PackPath = RootPath / "re/Fusion/RimFilletPack"
    SourcePath = (
        PackPath
        / ("Sources" if CaseName in KCaseNames else "Qualification/Archives")
        / CaseName
        / "Native.f3d"
    )
    SourceHash = HashBytes(SourcePath.read_bytes()).hexdigest()
    OutputPath = TmpPath / "Cycle"
    Result = RunProcess(
        [
            KPythonPath,
            str(PackPath / "ReadWrite.py"),
            str(RootPath),
            str(SourcePath),
            str(OutputPath),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    Receipt = LoadJson((OutputPath / "Receipt.json").read_bytes())
    assert Receipt["status"] == "passed" and Receipt["model_equal"] is True
    assert Receipt["source_sha256"] == SourceHash
    assert Receipt["source_snapshot_widths"] == Receipt["output_snapshot_widths"]
    assert HashBytes(SourcePath.read_bytes()).hexdigest() == SourceHash
    assert (OutputPath / "Reconstructed.f3d").is_file()
