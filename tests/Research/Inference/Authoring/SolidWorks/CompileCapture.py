# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from contextlib import AbstractContextManager
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path
from subprocess import CompletedProcess, run
from sys import platform

from pytest import skip

from tests.Research.SupervisorClient import KRepoRoot


# the actual native interop compiler validates the additive authoring contract without launching cad
def CompileCapture(CasePath: Path, OutputPath: Path) -> CompletedProcess[str]:
    if platform != "win32":
        skip("SOLIDWORKS interop compilation requires native Windows")
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
        skip("SOLIDWORKS registered native installation is unavailable")
    Interop = ExePath.parent / "api/redist/SolidWorks.Interop.sldworks.dll"
    if not Interop.is_file():
        skip("SOLIDWORKS registered interop assembly is unavailable")
    ShellPath = (
        Path(environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    ScriptPath = (
        KRepoRoot / "re/automation/CaptureTools/Catalogue/SolidWorks/RunSolidWorks.ps1"
    )
    return run(
        [
            str(ShellPath),
            "-NoProfile",
            "-NonInteractive",
            "-STA",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ScriptPath),
            "-CasePath",
            str(CasePath),
            "-OutputDirectory",
            str(OutputPath),
            "-ExecutablePath",
            str(ExePath),
            "-InteropAssembly",
            str(Interop),
            "-Phase",
            "first",
            "-CompileOnly",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
