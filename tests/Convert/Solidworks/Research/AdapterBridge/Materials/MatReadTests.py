from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# the isolated adapter process must keep standard view rounding separate from arbitrary camera changes
def CheckMatCold() -> None:
    RootPath = FilePath(__file__).resolve().parents[6]
    ProbePath = RootPath / "re/tooling/sw2026/materials/ProbeColdMatViews.py"
    ResultValue = RunProcess(
        (PythonExe, "-I", "-B", str(ProbePath)),
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert ResultValue.returncode == 0, ResultValue.stderr
    Report = LoadJson(ResultValue.stdout)
    assert Report["passed"] is True
    assert Report["strict_full_reads"] == 2
    assert Report["unrelated_camera_refusals"] == 1
    assert Report["unrepresented_stream_refusals"] == 1
    assert Report["runtime_reads"] == 0
    assert Report["native_processes_started"] == 0
