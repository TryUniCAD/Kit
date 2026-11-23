import sys
from collections.abc import Iterator
from contextlib import contextmanager as ContextScope
from secrets import token_hex as TokenHex

from tests.Research.Windows.Cli.StopCustody import StopCustody

if sys.platform == "win32":
    from win32api import GetLastError
    import win32job as WindowsJobs


# private custody must survive console leader exit and terminate descendants when its parent disappears
@ContextScope
def OwnConsole() -> Iterator[tuple[str, int]]:
    if sys.platform == "win32":
        JobName = "Local\\KitCliConsole-" + TokenHex(24)
        JobHandle = WindowsJobs.CreateJobObject(None, JobName)
        if GetLastError() == 183:
            JobHandle.Close()
            raise OSError("Private console custody name already exists")
        try:
            LimitsInfo = WindowsJobs.QueryInformationJobObject(
                JobHandle, WindowsJobs.JobObjectExtendedLimitInformation
            )
            LimitsInfo["BasicLimitInformation"]["LimitFlags"] = (
                WindowsJobs.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            WindowsJobs.SetInformationJobObject(
                JobHandle, WindowsJobs.JobObjectExtendedLimitInformation, LimitsInfo
            )
            yield JobName, int(JobHandle)
        finally:
            try:
                StopCustody(int(JobHandle))
            finally:
                JobHandle.Close()
    else:
        raise OSError("Private console custody requires Windows")
