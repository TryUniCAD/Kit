from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from tests.CliResearch.ResearchClient import ResearchCli


@TestMark.parametrize(
    "RootFlag", ("--r", "--ro", "--roo", "--root", "--roo=other", "--root=other")
)
def CheckRootPrefix(RootFlag: str, TmpPath: FilePath) -> None:
    Result = ResearchCli(
        TmpPath,
        "corpus",
        "check",
        RootFlag,
        str(TmpPath),
        "--manifest",
        str(TmpPath / "Manifest.json"),
    )
    assert Result.returncode == 1 and "--root once" in Result.stderr


def CheckRootGuard(TmpPath: FilePath) -> None:
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            "-m",
            "convert",
            "research",
            "--root",
            str(TmpPath),
            "solidworks",
            "--help",
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 1 and "requested PR94 research tool" in Result.stderr
    Unknown = ResearchCli(TmpPath, "unknown", "--help")
    assert Unknown.returncode == 2
    HelpResult = ResearchCli(TmpPath, "controller", "--help")
    assert HelpResult.returncode == 0 and "submit-batch" in HelpResult.stdout
