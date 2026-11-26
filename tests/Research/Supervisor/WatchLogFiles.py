from contextlib import suppress as Suppress
import subprocess as Subprocess
import time as TimeClock
from pathlib import Path as FilePath


# a final receipt alone cannot show whether retained logs stayed bounded during execution
def WatchLogFiles(Running: Subprocess.Popen[str], SessionPath: FilePath) -> None:
    UntilTime = TimeClock.monotonic() + 30
    while Running.poll() is None and TimeClock.monotonic() < UntilTime:
        for LogFile in SessionPath.glob("*.log"):
            with Suppress(FileNotFoundError):
                assert LogFile.stat().st_size <= 8192
        TimeClock.sleep(0.05)
    OutputText, ErrorText = Running.communicate(timeout=30)
    assert Running.returncode == 0, (OutputText, ErrorText)
