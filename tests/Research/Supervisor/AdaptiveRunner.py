import json as JsonCodec
import signal as Signals
import sys as System
import time as TimeClock
from tests.Research.Supervisor.SessionRoot import SessionRoot


# adaptive scheduling needs predictable workers that can finish normally or survive graceful shutdown
def RunAdaptive() -> None:
    SessionPath = SessionRoot(System.argv[1])
    JobText = (SessionPath / "job.json").read_text(encoding="utf-8")
    SessionInfo = JsonCodec.loads(JobText)
    Options = SessionInfo["job"]["options"]
    if Options.get("mode") == "deadline":
        _ = Signals.signal(Signals.SIGTERM, Signals.SIG_IGN)
        TimeClock.sleep(120)
        return
    TimeClock.sleep(float(Options.get("hold_seconds", 1)))
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "adaptive fixture finished",
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
    RunAdaptive()
