# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from ctypes import c_uint as UnsignedCount, c_wchar_p as TextPointer
from ctypes import create_unicode_buffer as MakeBuffer
from importlib import import_module as ImportModule
from pathlib import Path
from sys import platform
from typing import Callable, cast as CastValue


# native compiler invocation must use the operating system installation rather than caller controlled environment paths
def SystemShell() -> Path:
    if platform != "win32":
        raise OSError("the native compiler requires Windows")
    LoadLibrary = CastValue(
        Callable[[str], object], getattr(ImportModule("ctypes"), "WinDLL")
    )
    Kernel = LoadLibrary("kernel32")
    ReadSystem = CastValue(
        Callable[[object, int], int], getattr(Kernel, "GetSystemDirectoryW")
    )
    setattr(ReadSystem, "argtypes", [TextPointer, UnsignedCount])
    setattr(ReadSystem, "restype", UnsignedCount)
    Buffer = MakeBuffer(32768)
    Length = ReadSystem(Buffer, len(Buffer))
    if not 0 < Length < len(Buffer):
        raise OSError("the Windows system directory API returned an invalid length")
    ShellPath = (Path(Buffer.value) / "WindowsPowerShell/v1.0/powershell.exe").resolve(
        strict=True
    )
    if not ShellPath.is_file():
        raise FileNotFoundError(ShellPath)
    return ShellPath
