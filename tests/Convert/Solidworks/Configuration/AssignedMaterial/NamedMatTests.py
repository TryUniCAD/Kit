from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import KMeasureRoot


# a material stream cannot assign an unowned density to an ordinary saved solid
def TestNamedMat() -> None:
    ScriptPath = KMeasureRoot / "re/tooling/sw2026/materials/CheckNamedMaterialQueue.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ScriptPath)),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Expected = (
        "SOLIDWORKS assigned material density is absent, overridden or inconsistent"
    )
    assert LoadJson(Outcome.stdout) == {"design": Expected, "geometry": Expected}
