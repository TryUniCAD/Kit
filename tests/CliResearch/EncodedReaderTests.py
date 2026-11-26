from json import loads as DecodeJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchRoot import ResearchRoot


# stream overrides must never suppress native verification for a capable research reader
def CheckEncoded(TmpPath: FilePath) -> None:
    Target = TmpPath / "EncodedRead"
    Result = RunProcess(
        [
            str(
                FilePath(KPythonPath).with_name(
                    "kit.exe" if KPlatform == "win32" else "kit"
                )
            ),
            "research",
            "--root",
            str(ResearchRoot()),
            "solidworks",
            "--asset",
            KSwAsset,
            "--output",
            str(Target),
        ],
        env={
            **KEnvironment,
            "PYTHONIOENCODING": "utf-16le",
            "KIT_NATIVE_API_DIRECTORY": str(TmpPath / "NativeApi"),
        },
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert Result.returncode == 4, Result.stderr
    Summary = DecodeJson(Result.stdout.decode("utf-16le"))
    assert Summary["native_verification"]["status"] == "api_unavailable"
    Native = DecodeJson((Target / "NativeVerification.json").read_bytes())
    assert Native["status"] == "api_unavailable" and Native["action"]
