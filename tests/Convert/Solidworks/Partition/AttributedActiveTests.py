from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonExec


# the installed adapter must retain measured attributed topology and reject unsupported native state
def TestAttributed(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    ProbePath = RootPath / "re/tooling/sw2026/attributed_read/CheckAttributedRead.py"
    Outcome = RunProcess(
        (KPythonExec, "-I", "-B", str(ProbePath), "--output", str(TmpPath)),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert Outcome.returncode == 0, Outcome.stderr + Outcome.stdout
    assert (TmpPath / "AttributedRead.json").read_text(
        encoding="utf-8"
    ) == Outcome.stdout
    Evidence = LoadJson(Outcome.stdout)
    assert Evidence["topology"] == [6, 12, 8]
    assert Evidence["attribute_owners"] == 33
    assert Evidence["attribute_values"] == 32
    assert Evidence["all_faults_refused"] is True
    assert Evidence["native_launches"] == 0
