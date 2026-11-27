from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as TestMark


# superseded metadata runs must not alter latest title semantics or serialize required checks behind obsolete heads
@TestMark.parametrize("CaseMode", ("breaking", "remove", "unchanged"))
def CheckLabelFlow(CaseMode: str) -> None:
    ScriptPath = FilePath(__file__).with_name("RunBreaking.cjs")
    Outcome = RunProcess(
        ["node", str(ScriptPath), CaseMode],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
