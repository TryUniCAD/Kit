from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# complete distance graphs and native containers must cross a fresh interpreter boundary using neutral stdin alone
def RunSdkDistance(
    BundleValue: dict[str, object],
    ModeValue: str = "sdk",
    FaultValue: str | None = None,
) -> dict[str, object]:
    ResultValue = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/SdkDistanceMateProcess.py"),
        ],
        cwd=KRepoRoot,
        input=DumpJson({"mode": ModeValue, "bundle": BundleValue, "fault": FaultValue}),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    return CastValue(dict[str, object], LoadJson(ResultValue.stdout))
