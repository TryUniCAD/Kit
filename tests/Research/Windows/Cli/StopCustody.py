import sys

if sys.platform == "win32":
    from win32job import TerminateJobObject


# cleanup must reach owned descendants even after their console leader has already exited
def StopCustody(JobHandle: int) -> None:
    if sys.platform == "win32":
        TerminateJobObject(JobHandle, 1)
    else:
        raise OSError("Console custody termination requires Windows")
