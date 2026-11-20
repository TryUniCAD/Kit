from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath


# trusted historical checkouts must decode before unsupported verification flags can reject their inputs
def CanNativeVerify(ScriptPath: FilePath) -> bool:
    Result = RunProcess(
        [KPythonPath, str(ScriptPath), "--help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if Result.returncode:
        raise ValueError(
            "Selected research reader did not advertise its CLI capabilities"
        )
    return "--native-verify" in Result.stdout
