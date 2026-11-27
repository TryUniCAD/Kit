# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from subprocess import TimeoutExpired
from pathlib import Path

from CaptureTools.Catalogue.SolidWorks.NativeSolidEnv import NativeSolidEnv
from CaptureTools.Catalogue.SolidWorks.SolidPhaseFault import SolidPhaseFault
from CaptureTools.Catalogue.SolidWorks.SolidRecovery import RPC_LOST, SHUTDOWN_TIMEOUT, SolidRecovery


# a dedicated job bounds native descendants without touching other application sessions
def RunSolidPhase(CasePath, OutputPath, HostConfig, PhaseName, IsBatch=False):
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
    if IsBatch:
        Command.append("-Batch")
    Environment = NativeSolidEnv(HostConfig)
    with (
        (OutputPath / (PhaseName + ".log")).open("xb") as Output,
        (OutputPath / (PhaseName + ".stderr.log")).open("xb") as Errors,
    ):
        Process = WindowsProcess(
            Command, SourceRoot, Environment, Output.fileno(), Errors.fileno()
        )
        try:
            try:
                ExitCode = Process.wait(HostConfig.get("phase_seconds", 600))
            except TimeoutExpired:
                # A hung COM call can prevent PowerShell from reaching its shutdown handler.
                Process.signal(9)
                Process.wait(5)
                Process.finish()
                raise SolidRecovery(
                    SHUTDOWN_TIMEOUT, f"SOLIDWORKS {PhaseName} phase deadline expired; terminated owned job"
                ) from None
            Process.finish()
            if ExitCode:
                Output.flush()
                Errors.flush()
                Fault = SolidPhaseFault(OutputPath, PhaseName, ExitCode)
                if ExitCode in (RPC_LOST, SHUTDOWN_TIMEOUT):
                    raise SolidRecovery(ExitCode, Fault)
                raise Fault
        finally:
            Process.close()
