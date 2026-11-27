import ctypes as CTypes
import subprocess as Subprocess
import sys as System
from collections.abc import Callable
from ctypes import wintypes as WindowsTypes
from typing import cast

# ownership checks need the operating systems process snapshot flag
KProcessSnapshot = 2


# enumeration needs its normal end marker distinguished from native failures
KNoMoreFiles = 18


# native process rows provide parent identifiers without management provider startup
class ParentEntry(CTypes.Structure):
    pass


setattr(
    ParentEntry,
    "_fields_",
    [
        ("dwSize", WindowsTypes.DWORD),
        ("cntUsage", WindowsTypes.DWORD),
        ("th32ProcessID", WindowsTypes.DWORD),
        ("th32DefaultHeapID", CTypes.c_size_t),
        ("th32ModuleID", WindowsTypes.DWORD),
        ("cntThreads", WindowsTypes.DWORD),
        ("th32ParentProcessID", WindowsTypes.DWORD),
        ("pcPriClassBase", WindowsTypes.LONG),
        ("dwFlags", WindowsTypes.DWORD),
        ("szExeFile", WindowsTypes.WCHAR * 260),
    ],
)


# owner checks need an independent parent observation to associate a gate with the supervisor
def ReadParent(ProcessId: int) -> int | None:
    if System.platform == "win32":
        return ReadWinParent(ProcessId)
    Result = Subprocess.run(
        ["ps", "-p", str(ProcessId), "-o", "ppid="],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if Result.returncode == 1 and not Result.stdout.strip():
        return None
    assert Result.returncode == 0 and Result.stdout.strip().isdigit(), Result.stderr
    return int(Result.stdout.strip())


# snapshots avoid starting a management provider for every windows parent observation
def ReadWinParent(ProcessId: int) -> int | None:
    Loader = cast(
        Callable[[str, int, object, bool, bool], object],
        getattr(CTypes, "WinDLL"),
    )
    Kernel = Loader("kernel32", 0, None, False, True)
    Snapshot = cast(
        Callable[[int, int], int | None],
        getattr(Kernel, "CreateToolhelp32Snapshot"),
    )
    setattr(Snapshot, "argtypes", (WindowsTypes.DWORD, WindowsTypes.DWORD))
    setattr(Snapshot, "restype", WindowsTypes.HANDLE)
    Handle = Snapshot(KProcessSnapshot, 0)
    if Handle == CTypes.c_void_p(-1).value:
        raise OSError(ReadError(), "could not create the windows process snapshot")
    if Handle is None:
        raise OSError(ReadError(), "could not create the windows process snapshot")
    return ReadSnapshot(Kernel, Handle, ProcessId)


# native failures need their operating system error while missing processes remain ordinary
def ReadError() -> int:
    GetError = cast(Callable[[], int], getattr(CTypes, "get_last_error"))
    return GetError()


# each snapshot handle closes even when an owner lookup raises
def ReadSnapshot(Kernel: object, Handle: int, ProcessId: int) -> int | None:
    Closer = cast(Callable[[int], int], getattr(Kernel, "CloseHandle"))
    setattr(Closer, "argtypes", (WindowsTypes.HANDLE,))
    setattr(Closer, "restype", WindowsTypes.BOOL)
    try:
        return FindParent(Kernel, Handle, ProcessId)
    finally:
        SetError(0)
        if not Closer(Handle):
            raise OSError(ReadError(), "could not close the windows process snapshot")


# error state must reset before each native enumeration call
def SetError(ErrorCode: int) -> None:
    SetLastError = cast(Callable[[int], None], getattr(CTypes, "set_last_error"))
    SetLastError(ErrorCode)


# snapshot traversal distinguishes a missing process from native enumeration failures
def FindParent(Kernel: object, Handle: int, ProcessId: int) -> int | None:
    First = cast(Callable[[object, object], int], getattr(Kernel, "Process32FirstW"))
    Following = cast(Callable[[object, object], int], getattr(Kernel, "Process32NextW"))
    for ReadEntry in (First, Following):
        setattr(
            ReadEntry,
            "argtypes",
            (WindowsTypes.HANDLE, CTypes.POINTER(ParentEntry)),
        )
        setattr(ReadEntry, "restype", WindowsTypes.BOOL)
    Entry = ParentEntry()
    setattr(Entry, "dwSize", CTypes.sizeof(Entry))
    EntryPointer = CTypes.pointer(Entry)
    SetError(0)
    Found = First(Handle, EntryPointer)
    while Found:
        if int(getattr(Entry, "th32ProcessID")) == ProcessId:
            return int(getattr(Entry, "th32ParentProcessID"))
        SetError(0)
        Found = Following(Handle, EntryPointer)
    ErrorCode = ReadError()
    if ErrorCode == KNoMoreFiles:
        return None
    raise OSError(ErrorCode, "could not enumerate the windows process snapshot")
