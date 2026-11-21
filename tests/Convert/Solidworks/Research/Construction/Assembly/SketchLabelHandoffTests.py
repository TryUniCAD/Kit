from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the shared planner needs independent ordinary explicit and refused neutral processes
KLabelProbe = "re/tooling/sw2026/planar_registry/ProvePlanarLabelHandoff.py"


# this boundary must preserve the actual child owners while changing only their resolved labels
def TestSketchLabel() -> None:
    RootPath = FilePath(__file__).resolve().parents[6]
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(RootPath / KLabelProbe), "smoke"),
        capture_output=True,
        check=False,
        encoding="utf-8",
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["pass"] is True
    assert Report["guarded_workers"] == 3
    assert Report["runtime_input_reads"] == 0
    assert Report["changed_child_streams"] == ["Contents/Config-0-ResolvedFeatures"]
