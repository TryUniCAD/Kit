from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.CliResearch.RimFillets.CaseNames import KCaseNames


# real native archives must retain their complete typed model across a fresh reader writer process
@TestMark.parametrize("CaseName", KCaseNames)
def CheckRimCycle(TmpPath: FilePath, CaseName: str) -> None:
    RootPath = ResearchRoot()
    PackPath = RootPath / "re/Fusion/RimFilletPack"
    SourcePath = PackPath / "Sources" / CaseName / "Native.f3d"
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
    Receipt = LoadJson((OutputPath / "Receipt.json").read_bytes())
    Expected = LoadJson((PackPath / "ReadWriteContract.json").read_bytes())[CaseName]
    if Expected == "refused":
        assert Result.returncode == 2, Result.stderr
        assert "Unsupported Fusion snapshot header" in Receipt["traceback"]
        assert not (OutputPath / "Reconstructed.f3d").exists()
        return
    assert Result.returncode == 0, Result.stderr
    assert Receipt["model_equal"] is True
    assert Receipt["source_sha256"] == SourceHash
    assert Receipt["source_snapshot_widths"] == Receipt["output_snapshot_widths"]
    assert HashBytes(SourcePath.read_bytes()).hexdigest() == SourceHash
    assert (OutputPath / "Reconstructed.f3d").is_file()
