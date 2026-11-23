# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ctypes
import sys
from contextlib import ExitStack, contextmanager
from ctypes import wintypes

# the shared oracle lease also protects standalone authoring and research runs
OracleMutex = r"Local\KitResearchControllerOracle"

# priority survives between polls while windows automatically releases it on watcher exit
BatchPriorityMutex = r"Local\KitResearchControllerReadbackPriority"


# process enumeration uses the native executable name without inspecting process memory
class ProcessEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


# native admission must release the mutex even when an owner exits or fails
@contextmanager
def HoldMutex(Name, TimeoutMs=0):
    if sys.platform != "win32":
        raise ValueError("SOLIDWORKS application admission requires Windows")
    import win32event

    Mutex = win32event.CreateMutex(None, False, Name)
    try:
        Result = win32event.WaitForSingleObject(Mutex, TimeoutMs)
        if Result == win32event.WAIT_TIMEOUT:
            yield False
            return
        if Result not in (win32event.WAIT_OBJECT_0, win32event.WAIT_ABANDONED):
            raise ValueError("unexpected SOLIDWORKS application mutex state")
        try:
            yield True
        finally:
            win32event.ReleaseMutex(Mutex)
    finally:
        Mutex.Close()


# some sessions launch independently of the shared lease and still own the application
def IsSolidWorksRunning():
    Kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    Snapshot = Kernel.CreateToolhelp32Snapshot
    Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    Snapshot.restype = wintypes.HANDLE
    First, Next, Close = (
        Kernel.Process32FirstW,
        Kernel.Process32NextW,
        Kernel.CloseHandle,
    )
    for ReadEntry in (First, Next):
        ReadEntry.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry))
        ReadEntry.restype = wintypes.BOOL
    Close.argtypes = (wintypes.HANDLE,)
    Close.restype = wintypes.BOOL
    Handle = Snapshot(2, 0)  # TH32CS_SNAPPROCESS
    if Handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        Entry = ProcessEntry()
        Entry.dwSize = ctypes.sizeof(Entry)
        Found = First(Handle, ctypes.byref(Entry))
        while Found:
            if Entry.szExeFile.casefold() == "sldworks.exe":
                return True
            Found = Next(Handle, ctypes.byref(Entry))
        Error = ctypes.get_last_error()
        if Error != 18:  # ERROR_NO_MORE_FILES
            raise ctypes.WinError(Error)
        return False
    finally:
        Close(Handle)


# earlier launchers yield before taking the oracle while a readback is due
@contextmanager
def HoldEarlierStage(TimeoutMs=0):
    with ExitStack() as Oracle:
        with HoldMutex(BatchPriorityMutex, TimeoutMs) as PriorityFree:
            OracleFree = PriorityFree and Oracle.enter_context(HoldMutex(OracleMutex))
        yield OracleFree
