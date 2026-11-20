# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from pathlib import Path
from subprocess import CompletedProcess, run
from sys import platform

from pytest import skip

from tests.Research.SupervisorClient import KRepoRoot


# the actual native interop compiler validates the additive authoring contract without launching cad
def CompileCapture(CasePath: Path, OutputPath: Path) -> CompletedProcess[str]:
    if platform != "win32":
        skip("SOLIDWORKS interop compilation requires native Windows")
    from winreg import HKEY_CLASSES_ROOT, OpenKey, QueryValue

    try:
        with OpenKey(HKEY_CLASSES_ROOT, r"SldWorks.Application\CLSID") as KeyValue:
            ClassId = QueryValue(KeyValue, None)
        with OpenKey(
            HKEY_CLASSES_ROOT, "CLSID\\" + ClassId + r"\LocalServer32"
        ) as KeyValue:
            ExePath = Path(QueryValue(KeyValue, None)).resolve(strict=True)
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
