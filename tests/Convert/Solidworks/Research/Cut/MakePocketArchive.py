from base64 import b64decode as DecodeBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# the default reader regression starts from a newly authored neutral pocket in a guarded writer process
def MakePocketFile(OutputPath: FilePath) -> bytes:
    Tools = KRepoRoot / "re" / "tooling" / "sw2026"
    RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(Tools / "AuthorSdkPocketInputs.py"),
            str(OutputPath),
            "--native-directory",
            r"C:\KitNoCacheTests",
            "--written-at",
            "1794001000",
        ],
        check=True,
        timeout=120,
    )
    Request = (OutputPath / "SdkPocketFree.Request.json").read_bytes()
    Output = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(Tools / "SdkPocketProcess.py"),
            str(KRepoRoot),
            "build",
        ],
        input=Request,
        capture_output=True,
        check=True,
        timeout=120,
    )
    Report = LoadJson(Output.stdout)
    assert Report["passed"] is True and Report["runtime_input_file_reads"] == 0
    return DecodeBytes(Report["generated"], validate=True)
