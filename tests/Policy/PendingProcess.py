from __future__ import annotations as Annotations

import queue as QueueLib
import subprocess as Subprocess
import threading as ThreadLib
from pathlib import Path as FilePath
from time import monotonic as ReadClock
from typing import IO as StreamIO, Mapping

import pytest as Pytest

# shared runner contention must not consume the pending state observation window
KStartupWait = 30.0

# pending checks must stay blocked after their expected state becomes observable
KPendingWait = 2.0

# terminated children and output readers need bounded cleanup before the next probe
KCleanupWait = 5.0


# draining output prevents child pipe pressure from changing pending behavior
def ReadLines(StreamInfo: StreamIO[bytes], LineQueue: QueueLib.Queue[bytes]) -> None:
    try:
        for LineInfo in StreamInfo:
            LineQueue.put(LineInfo)
    finally:
        LineQueue.put(b"")


# the expected wait message distinguishes startup latency from aggregate readiness defects
def WaitSignal(LineQueue: QueueLib.Queue[bytes], PendingCheck: str) -> None:
    ExpectedText = f"Waiting for {PendingCheck}".encode()
    OutputData = bytearray()
    Deadline = ReadClock() + KStartupWait
    while ExpectedText not in OutputData:
        RemainSecs = Deadline - ReadClock()
        FailureText = f"CI aggregate never waited for {PendingCheck}\n"
        if RemainSecs <= 0:
            raise AssertionError(FailureText + OutputData.decode(errors="replace"))
        try:
            LineInfo = LineQueue.get(timeout=RemainSecs)
        except QueueLib.Empty as ErrorInfo:
            FailureText += OutputData.decode(errors="replace")
            raise AssertionError(FailureText) from ErrorInfo
        FailureText = f"CI aggregate stopped before waiting for {PendingCheck}\n"
        assert LineInfo, FailureText + OutputData.decode(errors="replace")
        OutputData.extend(LineInfo)


# command probes need observable pending state before asserting continued liveness
def WaitPending(
    ArgList: list[str],
    WorkPath: FilePath,
    EnvValues: Mapping[str, str],
    PendingCheck: str,
) -> None:
    with Subprocess.Popen(
        ArgList,
        cwd=WorkPath,
        env=EnvValues,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.STDOUT,
    ) as ProcessInfo:
        StdoutInfo = ProcessInfo.stdout
        assert StdoutInfo is not None
        LineQueue = QueueLib.Queue[bytes]()
        ReaderInfo = ThreadLib.Thread(
            target=ReadLines, args=(StdoutInfo, LineQueue), daemon=True
        )
        ReaderInfo.start()
        try:
            WaitSignal(LineQueue, PendingCheck)
            with Pytest.raises(Subprocess.TimeoutExpired):
                _ = ProcessInfo.wait(timeout=KPendingWait)
        finally:
            if ProcessInfo.poll() is None:
                ProcessInfo.kill()
            _ = ProcessInfo.wait(timeout=KCleanupWait)
            ReaderInfo.join(timeout=KCleanupWait)
            assert not ReaderInfo.is_alive()
