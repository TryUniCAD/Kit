from json import dumps as EncodeJson
from pathlib import Path as FilePath
from shutil import copytree as CopyTree


# complete and corrupted artifact sets exercise the actual reporter without substituting its implementation
def WriteReports(TmpPath: FilePath, Outcome: str) -> None:
    NodeNames = [f"tests/Native/ProbeTests.py::CheckCase{Index}" for Index in range(4)]
    for ShardIndex, NodeName in enumerate(NodeNames, 1):
        Attempt = 2 if Outcome in ("rerun", "latest-failed") and ShardIndex == 1 else 1
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
        Records: list[dict[str, str | int]] = [
            TestRecord,
            {"$report_type": "SessionFinish", "exitstatus": 0},
        ]
        if Outcome == "native":
            TestRecord.update(when="setup", outcome="skipped")
        if ShardIndex == 1:
            if Outcome == "missing":
                continue
            if Outcome == "duplicate":
                Records.append(TestRecord)
            if Outcome in ("failed", "latest-failed"):
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
        if Outcome in ("rerun", "latest-failed") and ShardIndex == 1:
            _ = (
                CopyTree(ReportPath, TmpPath / "Platform-shard-1-1") / "Report.jsonl"
            ).write_text(
                "{}\n"
                if Outcome == "rerun"
                else (ReportPath / "Report.jsonl")
                .read_text()
                .replace('"failed"', '"passed"')
            )
