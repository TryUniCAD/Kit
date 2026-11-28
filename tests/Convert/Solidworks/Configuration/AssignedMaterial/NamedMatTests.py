from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import KMeasureRoot


# the saved part can assign its proved physical material while both partial and invalid material writes refuse
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
    Rejection = (
        "SOLIDWORKS assigned material density is absent, overridden or inconsistent"
    )
    Assignment = ["sldprt:material:258", 2700.0, None, "sldprt:material:258"]
    assert LoadJson(Outcome.stdout) == {
        "assignment": {"design": Assignment, "geometry": Assignment},
        "invalid_assignment": {"design": Rejection, "geometry": Rejection},
        "writes_refused": 8,
        "json_material_states_preserved": 8,
    }
