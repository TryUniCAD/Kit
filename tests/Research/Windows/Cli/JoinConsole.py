import sys
from pathlib import Path as FilePath
from re import fullmatch as FullMatch

if sys.platform == "win32":
    from win32api import GetCurrentProcess
    import win32job as WindowsJobs


# the actual interpreter must join custody before spawning despite an external virtual environment redirector
def JoinConsole(RecordPath: FilePath) -> None:
    if sys.platform == "win32":
        JobName = RecordPath.with_name("ConsoleCustody").read_text(encoding="utf-8")
        if FullMatch(r"Local\\KitCliConsole-[0-9a-f]{48}", JobName) is None:
            raise ValueError("Invalid private console custody identity")
        AccessMask = (
            WindowsJobs.JOB_OBJECT_ASSIGN_PROCESS | WindowsJobs.JOB_OBJECT_QUERY
        )
        JobHandle = getattr(WindowsJobs, "OpenJobObject")(AccessMask, False, JobName)
        try:
            ProcessHandle = GetCurrentProcess()
            WindowsJobs.AssignProcessToJobObject(JobHandle, ProcessHandle)
            if not WindowsJobs.IsProcessInJob(ProcessHandle, JobHandle):
                raise OSError("Console helper did not join private custody")
        finally:
            JobHandle.Close()
    else:
        raise OSError("Joining console custody requires Windows")
