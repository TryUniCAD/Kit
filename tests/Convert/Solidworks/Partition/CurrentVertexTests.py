from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonExec


# the installed public sdk must recover the disclosed collision without changing successful readers
def TestVertexRead(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    ProbePath = RootPath / "re/tooling/sw2026/vertex_read/CheckPublicVertexRead.py"
    Outcome = RunProcess(
        (KPythonExec, "-I", "-B", str(ProbePath), "--output", str(TmpPath)),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert Outcome.returncode == 0, Outcome.stderr + Outcome.stdout
    _ = (TmpPath / "VertexRead.json").write_text(Outcome.stdout, encoding="utf-8")
    Evidence = LoadJson(Outcome.stdout)
    assert Evidence["public_cases"] == 6
    assert Evidence["repaired_topology"] == [7, 15, 10]
    assert Evidence["legacy_successes_preserved"] == 5
    assert Evidence["native_launches"] == 0
