from json import dumps as DumpJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from re import search as SearchText
from subprocess import run as RunProcess
from textwrap import dedent as DedentText

from pytest import mark as TestMark

from tests.Policy.Shards.FindTestShell import FindTestShell


# the real gate command must retain its direct completeness dependencies without serializing an identical compatibility verdict
@TestMark.parametrize("CheckName", ("test-plan", "test-shard", "test-report"))
@TestMark.parametrize(
    "Verdict", ("success", "failure", "cancelled", "skipped", "timed_out", "pending")
)
def CheckTailGate(TmpPath: FilePath, CheckName: str, Verdict: str) -> None:
    WorkflowPath = (
        FilePath(__file__).resolve().parents[2] / ".github/workflows/MergeQueue.yml"
    )
    GateText = WorkflowPath.read_text(encoding="utf-8").split("  gate:\n", 1)[1]
    NeedsMatch = SearchText(r"needs:\s*\[([^]]+)\]", GateText)
    ScriptMatch = SearchText(r"        run: \|\n([\s\S]+)", GateText)
    assert NeedsMatch is not None and ScriptMatch is not None
    Needs = tuple(
        InputName.strip() for InputName in NeedsMatch[1].split(",") if InputName.strip()
    )
    assert "verify-end-to-end" not in Needs
    assert {"test-plan", "test-shard", "test-report"}.issubset(Needs)
    Outcomes = {InputName: {"result": "success"} for InputName in Needs}
    Outcomes[CheckName]["result"] = Verdict
    ScriptPath = TmpPath / "Gate.sh"
    _ = ScriptPath.write_text(DedentText(ScriptMatch[1]), encoding="utf-8")
    ExecuteGate(ScriptPath, Outcomes, TmpPath, Verdict == "success")


# executing the workflow command exposes accidental success masking at the actual shell and json validation boundary
def ExecuteGate(
    ScriptPath: FilePath,
    Outcomes: dict[str, dict[str, str]],
    TempRoot: FilePath,
    IsPassing: bool,
) -> None:
    Outcome = RunProcess(
        [FindTestShell(), ScriptPath.as_posix()],
        env={
            **KEnvironment,
            "EVENT_NAME": "merge_group",
            "JOB_RESULTS": DumpJson(Outcomes),
            "GITHUB_STEP_SUMMARY": (TempRoot / "Summary.md").as_posix(),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert (Outcome.returncode == 0) == IsPassing, Outcome.stdout + Outcome.stderr
