import hashlib as Hashing
import json as JsonCodec
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost

# the real registry must route the same job kinds configured by catalogue authoring
KCapture = "capture.catalogue.solidworks"

# the batch worker shares the same recovery policy but keeps separate dispatch identity
KBatch = "capture.catalogue.solidworks.batch"


# failed native attempts must preserve inputs and restart within budget while leaving other jobs runnable
def CheckRecovery() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RunRecovery(FilePath(TempPath))


# isolated durable queue receipts show which jobs were retried and which finished
def RunRecovery(RootPath: FilePath) -> None:
    Harness = SessionHost(
        RootPath, {"decode": 2}, {KCapture: "decode", KBatch: "decode"}
    )
    RegistryPath = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    for Runner in Registry["runners"].values():
        Runner["argv"] = [
            System.executable,
            "-m",
            "tests.Research.CaptureResilience.CaptureFixture",
            "{session}",
        ]
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Harness.BindBytes("fixture:case", b"capture inputs")
    JobList = [
        FixtureJob(
            ModeName,
            KindName,
            inputs={"case": "fixture:case"},
            options={"mode": ModeName},
            max_attempts=3,
        )
        for ModeName, KindName in (
            ("rpc", KCapture),
            ("always-rpc", KBatch),
            ("shutdown", KBatch),
            ("hung", KBatch),
            ("ok", KBatch),
        )
    ]
    Harness.SubmitJobs(JobList)
    Events = Harness.RunIdle(IdleSeconds=4)
    Summary = JsonCodec.loads(JsonCodec.dumps(Events[-1]))["summary"]
    assert Summary["finished"] == {"completed": 4, "rejected": 1, "retry": 4}, Events
    for JobName in ("rpc", "shutdown", "hung", "ok"):
        JobRow = Harness.ReadJob(JobName)
        assert JobRow["state"] == "completed", JobRow
        assert JobRow["attempts"] == (1 if JobName == "ok" else 2), JobRow
        Result = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult(JobName)))
        assert Result["result"]["records"]["inputs"] == [
            Hashing.sha256(b"capture inputs").hexdigest()
        ]
    Failed = Harness.ReadJob("always-rpc")
    assert Failed["state"] == "rejected" and Failed["attempts"] == 2, Failed
    assert "recovery attempt exhausted" in str(Failed["reason"])
    assert "exit 71" in str(Harness.ReadResult("always-rpc")["stderr_tail"])
