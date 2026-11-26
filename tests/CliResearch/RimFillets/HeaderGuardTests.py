from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from tests.CliResearch.ResearchRoot import ResearchRoot


# complete archive emission must preserve destinations when unsupported snapshot metadata would otherwise be discarded
@TestMark.parametrize(
    "FieldName",
    (
        "IntWidth",
        "Scale",
        "Flags",
        "RootCount",
        "AbsoluteTolerance",
        "NormalTolerance",
    ),
)
def CheckSnapGuard(TmpPath: FilePath, FieldName: str) -> None:
    RootPath = ResearchRoot()
    PackPath = RootPath / "re/Fusion/RimFilletPack"
    SourcePath = PackPath / "Sources/discovery-01/Native.f3d"
    SourceHash = HashBytes(SourcePath.read_bytes()).hexdigest()
    TargetPath = TmpPath / "Preserved.f3d"
    _ = TargetPath.write_bytes(b"preserved destination")
    Result = RunProcess(
        [
            KPythonPath,
            str(PackPath / "RefuseHeader.py"),
            "--root",
            str(RootPath),
            "--source",
            str(SourcePath),
            "--target",
            str(TargetPath),
            "--field",
            FieldName,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    assert "Unsupported Fusion snapshot header" in Result.stdout
    assert TargetPath.read_bytes() == b"preserved destination"
    assert HashBytes(SourcePath.read_bytes()).hexdigest() == SourceHash
