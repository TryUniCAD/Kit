# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from pathlib import Path


# a dedicated job bounds native descendants without touching other application sessions
def RunSolidPhase(CasePath, OutputPath, HostConfig, PhaseName):
    from WindowsProcess import WindowsProcess

    SourceRoot = Path(__file__).resolve().parents[5]
    ScriptPath = Path(__file__).with_name("RunSolidWorks.ps1")
    ShellPath = (
        Path(environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    Command = [
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
        "-InteropAssembly",
        HostConfig["interop_assembly"],
        "-ExecutablePath",
        HostConfig["executable"],
        "-Phase",
        PhaseName,
    ]
    Environment = {
        Name: Value
        for Name, Value in environ.items()
        if Name.casefold() != "psmodulepath"
    }
    with (
        (OutputPath / (PhaseName + ".log")).open("xb") as Output,
        (OutputPath / (PhaseName + ".stderr.log")).open("xb") as Errors,
    ):
        Process = WindowsProcess(
            Command, SourceRoot, Environment, Output.fileno(), Errors.fileno()
        )
        try:
            ExitCode = Process.wait(timeout=HostConfig.get("phase_seconds", 600))
            Process.finish()
            if ExitCode:
                raise RuntimeError(
                    "SOLIDWORKS authoring phase failed inspect " + str(Errors.name)
                )
        finally:
            Process.close()
