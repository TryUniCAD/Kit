from json import dumps as EncodeJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as TestMark


# published artifact corruption must block platform acceptance at the actual reporting process boundary
@TestMark.parametrize(
    "Outcome",
    (
        "passed",
        "missing",
        "duplicate",
        "failed",
        "session",
        "roster",
        "extra",
        "native",
        "rerun",
    ),
)
@TestMark.parametrize("NativePattern", ("", "^tests/Native/"))
def CheckShardGate(TmpPath: FilePath, Outcome: str, NativePattern: str) -> None:
    NodeNames = [f"tests/Native/ProbeTests.py::CheckCase{Index}" for Index in range(4)]
    for ShardIndex, NodeName in enumerate(NodeNames, 1):
        Attempt = 2 if Outcome == "rerun" and ShardIndex == 1 else 1
        ReportPath = TmpPath / f"Platform-shard-{ShardIndex}-{Attempt}"
        ReportPath.mkdir()
        _ = (ReportPath / "Collected.txt").write_text("\n".join(NodeNames) + "\n")
        _ = (ReportPath / "Selected.txt").write_text(NodeName + "\n")
        TestRecord: dict[str, str | int] = {
            "$report_type": "TestReport",
            "nodeid": NodeName,
            "when": "call",
            "outcome": "passed",
        }
        Records = [TestRecord, {"$report_type": "SessionFinish", "exitstatus": 0}]
        if Outcome == "native":
            TestRecord.update(when="setup", outcome="skipped")
        if ShardIndex == 1:
            if Outcome == "missing":
                continue
            if Outcome == "duplicate":
                Records.append(TestRecord)
            if Outcome == "failed":
                TestRecord["outcome"] = "failed"
            if Outcome == "session":
                Records[1]["exitstatus"] = 1
            if Outcome == "roster":
                _ = (ReportPath / "Collected.txt").write_text(NodeName + "\n")
            if Outcome == "extra":
                Records.append({**TestRecord, "nodeid": "tests/Unexpected::CheckCase"})
        _ = (ReportPath / "Report.jsonl").write_text(
            "\n".join(EncodeJson(Record) for Record in Records) + "\n"
        )
    Result = RunProcess(
        (
            "bash",
            str(
                FilePath(__file__).resolve().parents[2]
                / ".github/scripts/VerifyShardReports.sh"
            ),
            str(TmpPath),
            "Platform",
            "2" if Outcome == "rerun" else "1",
            NativePattern,
        ),
        env={**KEnvironment, "GITHUB_STEP_SUMMARY": str(TmpPath / "Summary.md")},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    ExpectedPass = Outcome in ("passed", "rerun") or (
        Outcome == "native" and not NativePattern
    )
    assert (Result.returncode == 0) == ExpectedPass, Result.stdout + Result.stderr
