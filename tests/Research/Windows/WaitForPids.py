import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from convert.Security.PathBoundary import ResolveTemp


# the test needs an independently recorded roster before it can verify tree cleanup
def WaitForPids(RecordPath: FilePath, Timeout: float = 30) -> list[int]:
    RecordPath = ResolveTemp(RecordPath)
    UntilTime = TimeClock.monotonic() + Timeout
    while TimeClock.monotonic() < UntilTime:
        try:
            ProcessIds: list[int] = JsonCodec.loads(
                RecordPath.read_text(encoding="utf-8")
            )
            assert len(ProcessIds) in (2, 3)
            assert len(set(ProcessIds)) == len(ProcessIds)
            assert all(
                type(ProcessId) is int and ProcessId > 1 for ProcessId in ProcessIds
            )
            return ProcessIds
        except (OSError, ValueError):
            TimeClock.sleep(0.05)
    raise AssertionError("Windows runner did not record process identities")
