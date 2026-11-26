# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import AbstractContextManager
from importlib import import_module as ImportModule
from pathlib import Path
from sys import platform
from typing import Callable, cast as CastValue

from pytest import skip


# native compiler checks require the registered executable and its matching installed interop assembly
def LoadInterop() -> tuple[Path, Path]:
    if platform != "win32":
        return skip("SOLIDWORKS interop compilation requires native Windows")
    Registry = ImportModule("winreg")
    ClassRoot = CastValue(int, getattr(Registry, "HKEY_CLASSES_ROOT"))
    OpenClass = CastValue(
        Callable[[int, str], AbstractContextManager[object]],
        getattr(Registry, "OpenKey"),
    )
    QueryClass = CastValue(
        Callable[[object, None], str], getattr(Registry, "QueryValue")
    )

    try:
        with OpenClass(ClassRoot, r"SldWorks.Application\CLSID") as KeyValue:
            ClassId = QueryClass(KeyValue, None)
        with OpenClass(ClassRoot, "CLSID\\" + ClassId + r"\LocalServer32") as KeyValue:
            ExePath = Path(QueryClass(KeyValue, None)).resolve(strict=True)
    except (OSError, FileNotFoundError):
        return skip("SOLIDWORKS registered native installation is unavailable")
    Interop = ExePath.parent / "api/redist/SolidWorks.Interop.sldworks.dll"
    if not Interop.is_file():
        return skip("SOLIDWORKS registered interop assembly is unavailable")
    return ExePath, Interop
