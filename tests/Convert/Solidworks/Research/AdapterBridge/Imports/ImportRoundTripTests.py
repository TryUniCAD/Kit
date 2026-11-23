from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# complete public import round trips need independent measured input and an isolated runtime guard
def CheckColdImportRoundTrip() -> None:
    RootPath = FilePath(__file__).resolve().parents[6]
    ProbePath = (
        RootPath / "re/tooling/sw2026/imported_body_source/VerifyColdImportRoundTrip.py"
    )
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
    assert Report["native_processes_started"] == 0
    assert set(Report["cases"]) == {"RectangularBare", "ConcaveOwned"}
    for Row in Report["cases"].values():
        assert Row["logical_streams"] == 12
        assert Row["runtime_reads"] == 0
        assert (Row["exact_writes"], Row["refusals"], Row["geometry_comparisons"]) in {
            (6, 21, 10),
            (0, 12, 15),
        }
