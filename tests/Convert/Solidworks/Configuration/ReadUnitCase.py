from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# a fresh process must consume the original table records through the shared codec
KUnitProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckUnitTables.py"
)


# the verifier runs inside the same integration boundary as the other archive process cases
def ReadUnitCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KUnitProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
