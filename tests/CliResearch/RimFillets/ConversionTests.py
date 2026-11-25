from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from pytest import mark as TestMark

from tests.CliResearch.ResearchRoot import ResearchRoot


# unresolved fillet semantics must refuse public conversion before creating a misleading native destination
@TestMark.parametrize("CaseName", ("discovery-01", "holdout-06"))
@TestMark.parametrize(
    "SourceKind,Message",
    (
        (
            "Native",
            "Native Fusion projection requires a sketch followed by one extrusion",
        ),
        ("Generated", "Unsupported native Fusion feature class"),
    ),
)
@TestMark.parametrize("TargetSuffix", ("f3d", "SLDPRT"))
def CheckRimGuard(
    TmpPath: FilePath, CaseName: str, SourceKind: str, Message: str, TargetSuffix: str
) -> None:
    PackPath = ResearchRoot() / "re/Fusion/RimFilletPack"
    SourcePath = PackPath / "Sources" / CaseName / (SourceKind + ".f3d")
    SourceHash = HashBytes(SourcePath.read_bytes()).hexdigest()
    OutputPath = TmpPath / ("Refused." + TargetSuffix)
    Launcher = FilePath(KPythonPath).with_name(
        "kit.exe" if KPlatform == "win32" else "kit"
    )
    Result = RunProcess(
        [str(Launcher), "convert", str(SourcePath), str(OutputPath), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 1, Result.stdout + Result.stderr
    assert Message in Result.stdout + Result.stderr
    assert not OutputPath.exists()
    assert HashBytes(SourcePath.read_bytes()).hexdigest() == SourceHash
