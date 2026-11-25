from json import loads as ReadJson
from os import environ as SystemEnv
from pathlib import Path
from subprocess import run as RunProcess
from sys import platform as Platform

from pytest import mark as PytestMark

from tests.Research.Inference.Authoring.SolidWorks.SystemShell import SystemShell
from tests.Research.SupervisorClient import KRepoRoot


# real powershell launch failures must stop at the retry limit and retain each original error
@PytestMark.skipif(Platform != "win32", reason="Windows startup process boundary")
def CheckStartRetry(TmpPath: Path) -> None:
    ScriptPath = (
        KRepoRoot
        / "re/automation/CaptureTools/Catalogue/SolidWorks/StartOwnedSolid.ps1"
    )
    Process = RunProcess(
        [
            str(SystemShell()),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$ErrorActionPreference='Stop'; . $env:KIT_RETRY_SCRIPT; "
            "Start-OwnedSolid -Executable ([IO.FileInfo]::new($env:KIT_RETRY_MISSING)) "
            "-Destination $env:KIT_RETRY_OUTPUT -Phase first",
        ],
        env={
            **SystemEnv,
            "KIT_RETRY_SCRIPT": str(ScriptPath),
            "KIT_RETRY_MISSING": str(TmpPath / "MissingExecutable.exe"),
            "KIT_RETRY_OUTPUT": str(TmpPath),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode != 0
    Receipt = ReadJson((TmpPath / "first-startup.json").read_bytes())
    assert Receipt["max_attempts"] == 3
    assert [Attempt["attempt"] for Attempt in Receipt["attempts"]] == [1, 2, 3]
    assert all(
        Attempt["ready"] is False and Attempt["error"]
        for Attempt in Receipt["attempts"]
    )
    assert Receipt["seconds"] >= 2
    assert Process.stdout.count("retrying") == 2
    assert not (TmpPath / "first-owner.json").exists()
