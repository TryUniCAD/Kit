import json as JsonCodec
import sys as System
import time as TimeClock
from pathlib import Path as FilePath
from tests.Research.Supervisor.SessionRoot import SessionRoot


# a session that exits between supervision passes has no process group sample to learn from
def AwaitSample(SessionPath: FilePath) -> None:
    Marker = f"sampled:{SessionPath.name}\n"
    _ = System.stdout.write(Marker)
    _ = System.stdout.flush()
    TimeClock.sleep(1)
    LogFile = SessionPath / "stdout.log"
    Until = TimeClock.monotonic() + 50
    while Marker not in LogFile.read_text(encoding="utf-8"):
        if TimeClock.monotonic() >= Until:
            raise TimeoutError("supervisor never drained the sample marker")
        TimeClock.sleep(0.05)


# the estimator needs a measurable memory sample from a successful real child process
def RunLearning() -> None:
    SessionPath = SessionRoot(System.argv[1])
    JobText = (SessionPath / "job.json").read_text(encoding="utf-8")
    Content = bytearray(2 * 1048576)
    for Offset in range(0, len(Content), 4096):
        Content[Offset] = 1
    AwaitSample(SessionPath)
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "measured fixture finished",
        "records": {
            "count": 1,
            "inputs": [],
            "tokenless": "lease_token" not in JobText,
        },
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    RunLearning()
