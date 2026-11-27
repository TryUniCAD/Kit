from pathlib import Path as FilePath
from re import split as SplitText
from subprocess import run as RunProcess

from pytest import mark as TestMark


# workflow integration must retain trusted marker failures while removing the dependent runner allocation from light validation
@TestMark.parametrize(
    "FlowName",
    (
        "PythonQuality",
        "PythonSteering",
        "PathPolicies",
        "RationaleComments",
        "ExplicitImports",
        "SteeringSync",
        "WorkflowPins",
        "WorkflowQuality",
    ),
)
@TestMark.parametrize("CaseMode", ("pull", "queue", "legacy", "denied", "invalid"))
def CheckInlineFlow(FlowName: str, CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    FlowPath = RootPath / f".github/workflows/{FlowName}.yml"
    SourceText = FlowPath.read_text(encoding="utf-8")
    Blocks = SplitText(r"(?m)^  [a-z][a-z-]*:\s*$", SourceText)[2:]
    DirectJobs = [Block for Block in Blocks if "    needs:" not in Block]
    assert DirectJobs
    assert "      - &ReadPhase" in SourceText
    assert "await SetPhase({ github, context, core });" in SourceText
    for Block in DirectJobs:
        assert "      - *ReadPhase" in Block
        assert (
            Block.index("      - *ReadPhase") < Block.index("      - name: Set up uv")
            if "      - name: Set up uv" in Block
            else True
        )
        Steps = SplitText(
            r"(?m)^      - name:", Block.split("      - *ReadPhase", 1)[1]
        )[1:]
        assert all(
            "if:" in CheckStep and "steps.phase.outputs.phase" in CheckStep
            for CheckStep in Steps
        )
        if not any(
            f"    name: {CheckName}\n" in Block
            for CheckName in ("Pyright", "Mypy", "Python steering")
        ):
            assert "    if: github.event_name == 'pull_request'" in Block
    Process = RunProcess(
        ["node", str(RootPath / "tests/Policy/CiAggregation/RunPhase.cjs"), CaseMode],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    IsPassing = CaseMode not in {"denied", "invalid"}
    assert (Process.returncode == 0) == IsPassing, Process.stdout + Process.stderr
    if IsPassing:
        assert (
            f"phase={ {'pull': 'pull_request', 'queue': 'merge_group', 'legacy': 'legacy'}[CaseMode]}"
            in Process.stdout
        )
