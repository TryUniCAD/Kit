import ctypes
import time
from collections import deque
from ctypes import wintypes

from WindowsApi import KERNEL, require_success


KERNEL.GetSystemTimes.argtypes = [ctypes.POINTER(wintypes.FILETIME)] * 3
KERNEL.GetSystemTimes.restype = wintypes.BOOL
KERNEL.GetActiveProcessorGroupCount.argtypes = []
KERNEL.GetActiveProcessorGroupCount.restype = wintypes.WORD

WINDOW_SECONDS = 60
MAX_WINDOW_SECONDS = 70


def ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


def system_cpu_times():
    idle, kernel, user = (wintypes.FILETIME() for _ in range(3))
    require_success(KERNEL.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)))
    return ticks(idle), ticks(kernel) + ticks(user)


class WindowsCpuLoad:
    def __init__(self):
        self.samples = deque(maxlen=32)

    def sample(self, covers_affinity):
        if not covers_affinity or KERNEL.GetActiveProcessorGroupCount() != 1:
            self.samples.clear()
            return None
        now = time.monotonic()
        try:
            idle, total = system_cpu_times()
        except OSError:
            self.samples.clear()
            return None
        if self.samples:
            previous_time, previous_idle, previous_total = self.samples[-1]
            if now <= previous_time or not 0 <= idle - previous_idle <= total - previous_total:
                self.samples.clear()
        self.samples.append((now, idle, total))
        while len(self.samples) > 1 and now - self.samples[1][0] >= WINDOW_SECONDS:
            self.samples.popleft()
        start, first_idle, first_total = self.samples[0]
        if not WINDOW_SECONDS <= now - start <= MAX_WINDOW_SECONDS or total == first_total:
            return None
        return 1 - (idle - first_idle) / (total - first_total)
