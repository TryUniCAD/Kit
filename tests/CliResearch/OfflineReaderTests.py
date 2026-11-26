from json import loads as LoadJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchRoot import ResearchRoot


# offline decoding must preserve real reader evidence without attempting application verification
def CheckOffline(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Target = TmpPath / "Decoded"
    Result = RunProcess(
        [
            str(
                FilePath(KPythonPath).with_name(
                    "kit.exe" if KPlatform == "win32" else "kit"
                )
            ),
            "research",
            "--offline",
            "--root",
            str(RootPath),
            "solidworks",
            "--asset",
            KSwAsset,
            "--output",
            str(Target),
        ],
        cwd=RootPath,
        env={
            **KEnvironment,
            "KIT_NATIVE_API_DIRECTORY": str(TmpPath / "NativeApi"),
        },
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 0, Result.stderr
    assert "native verification pending" in Result.stderr
    assert not (Target / "NativeVerification.json").exists()
    Receipt = LoadJson((Target / "receipt.json").read_bytes())
    assert Receipt["native_acceptance"] == "not_established"
    assert Receipt["portable_complete"] is False
    assert LoadJson((Target / "document.json").read_bytes())["$type"] == "CadDocument"


# abbreviated downstream flags must fail before any decoding or application access
def CheckConflict(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Target = TmpPath / "Conflict"
    for FlagText in ("--n", "--nativ", "--native-verify"):
        Result = RunProcess(
            [
                str(
                    FilePath(KPythonPath).with_name(
                        "kit.exe" if KPlatform == "win32" else "kit"
                    )
                ),
                "research",
                "--offline",
                "--root",
                str(RootPath),
                "solidworks",
                FlagText,
                "--asset",
                KSwAsset,
                "--output",
                str(Target),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert Result.returncode == 1, Result.stderr
        assert "cannot request native verification" in Result.stderr
        assert not Target.exists()
