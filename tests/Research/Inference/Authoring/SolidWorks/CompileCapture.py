# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from subprocess import CompletedProcess, run

from tests.Research.Inference.Authoring.SolidWorks.CompilerEnv import CompilerEnv
from tests.Research.Inference.Authoring.SolidWorks.NativeInterop import LoadInterop
from tests.Research.Inference.Authoring.SolidWorks.SystemShell import SystemShell
from tests.Research.SupervisorClient import KRepoRoot


# the actual native interop compiler validates the additive authoring contract without launching cad
def CompileCapture(CasePath: Path, OutputPath: Path) -> CompletedProcess[str]:
    ExePath, Interop = LoadInterop()
    ShellPath = SystemShell()
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
            "-Command",
            "& $env:KIT_COMPILE_SCRIPT -CasePath $env:KIT_COMPILE_CASE "
            + "-OutputDirectory $env:KIT_COMPILE_OUTPUT "
            + "-ExecutablePath $env:KIT_COMPILE_EXECUTABLE "
            + "-InteropAssembly $env:KIT_COMPILE_INTEROP -Phase first -CompileOnly",
        ],
        cwd=KRepoRoot,
        env=CompilerEnv(ScriptPath, CasePath, OutputPath, ExePath, Interop, ShellPath),
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
