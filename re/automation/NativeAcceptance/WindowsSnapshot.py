import ctypes
import ctypes.wintypes as wintypes
from contextlib import contextmanager
import msvcrt


class BasicInfo(ctypes.Structure):
    _fields_ = [("created", ctypes.c_int64), ("accessed", ctypes.c_int64), ("written", ctypes.c_int64), ("changed", ctypes.c_int64), ("attributes", wintypes.DWORD)]


class StandardInfo(ctypes.Structure):
    _fields_ = [("allocated", ctypes.c_int64), ("size", ctypes.c_int64), ("links", wintypes.DWORD), ("deleted", ctypes.c_ubyte), ("directory", ctypes.c_ubyte)]


class IdentityInfo(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_uint64), ("identity", ctypes.c_ubyte * 16)]


Kernel = ctypes.WinDLL("kernel32", use_last_error=True)
Kernel.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
Kernel.CreateFileW.restype = wintypes.HANDLE
Kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
Kernel.CloseHandle.restype = wintypes.BOOL
Kernel.GetFileType.argtypes = (wintypes.HANDLE,)
Kernel.GetFileType.restype = wintypes.DWORD
Kernel.GetFileInformationByHandleEx.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
Kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL


@contextmanager
def HoldPath(path):
    handle = Kernel.CreateFileW(str(path.absolute()), 0x80, 1, None, 3, 0x00200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        yield handle
    finally:
        if not Kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def Snapshot(handle):
    if Kernel.GetFileType(handle) != 1:
        raise ValueError("verification input must be a regular disk file")
    basic, standard, identity = BasicInfo(), StandardInfo(), IdentityInfo()
    for kind, value in ((0, basic), (1, standard), (18, identity)):
        if not Kernel.GetFileInformationByHandleEx(handle, kind, ctypes.byref(value), ctypes.sizeof(value)):
            raise ctypes.WinError(ctypes.get_last_error())
    if standard.directory or standard.deleted or standard.links != 1 or basic.attributes & (0x400 | 0x10 | 0x40):
        raise ValueError("verification input must be a regular file without links")
    if standard.size < 0 or not any(identity.identity):
        raise ValueError("verification input has no stable native file identity")
    return identity.volume, bytes(identity.identity), standard.size, basic.created, basic.written, basic.changed, basic.attributes, standard.links


def ReadWindows(path, limit):
    with HoldPath(path) as handle:
        before = Snapshot(handle)
        if before[2] > limit:
            raise ValueError("verification input changed or exceeded its byte limit")
        with path.open("rb") as stream:
            native_handle = msvcrt.get_osfhandle(stream.fileno())
            opened = Snapshot(native_handle)
            data = stream.read(limit + 1)
            after = Snapshot(native_handle)
        with HoldPath(path) as final_handle:
            final = Snapshot(final_handle)
        if len(data) > limit or len(data) != before[2] or not before == opened == after == final:
            raise ValueError("verification input changed or exceeded its byte limit")
        return data
