import ctypes
import os
from ctypes import wintypes

import win32api
import win32process
import pywintypes

from WindowsApi import KERNEL, require_success
from WindowsProcess import JOBS


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.DWORD), ("load", wintypes.DWORD),
        ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
        ("total_pagefile", ctypes.c_ulonglong), ("available_pagefile", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
        ("available_extended_virtual", ctypes.c_ulonglong),
    ]


KERNEL.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
KERNEL.GlobalMemoryStatusEx.restype = wintypes.BOOL


def host_resources(windows_cpu=None):
    memory = MemoryStatus()
    memory.length = ctypes.sizeof(memory)
    require_success(KERNEL.GlobalMemoryStatusEx(ctypes.byref(memory)))
    try:
        affinity, system_affinity = win32process.GetProcessAffinityMask(win32api.GetCurrentProcess())
    except pywintypes.error as error:
        raise OSError("Windows process CPU affinity unavailable") from error
    cpus = os.cpu_count()
    if cpus is None:
        raise OSError("Windows logical CPU count unavailable")
    logical_cpus = min(cpus, int(affinity).bit_count())
    if logical_cpus < 1:
        raise OSError("Windows process CPU affinity is empty")
    resources = {"logical_cpus": logical_cpus, "available_memory_bytes": memory.available_physical, "memory_source": "windows:GlobalMemoryStatusEx:ullAvailPhys"}
    if windows_cpu is not None:
        resources["cpu_busy_fraction_1m"] = windows_cpu.sample(affinity == system_affinity)
    return resources


def group_memory(pids):
    if any(pid not in JOBS for pid in pids):
        raise OSError("session Windows job identity unavailable")
    try:
        return {pid: JOBS[pid].memory() for pid in pids}
    except pywintypes.error as error:
        raise OSError("Windows job resource measurement unavailable") from error
