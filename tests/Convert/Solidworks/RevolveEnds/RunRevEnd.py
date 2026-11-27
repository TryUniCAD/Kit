from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from typing import cast as CastValue


# each measured or independently authored archive must cross an isolated sdk process
def RunRevEnd(ToolName: str, CaseValue: str, *FlagsValue: str) -> dict[str, object]:
    RootValue = FilePath(__file__).resolve().parents[4]
    ToolValue = RootValue / "re/tooling/sw2026/revolve" / ToolName
    Outcome = RunProcess(
        (Interpreter, "-I", "-B", str(ToolValue), "--case", CaseValue, *FlagsValue),
        cwd=RootValue,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Result = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Result["audit"] == {
        "input_file_reads": 0,
        "external_launches": 0,
        "output_opens": 0,
    }
    assert Result["case"] == CaseValue
    return Result
