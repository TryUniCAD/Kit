# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import contextmanager as ContextManager
from os import name as OsName
from pathlib import Path as FilePath
from signal import SIGINT as KInterrupt
from subprocess import (
    DEVNULL as KNullInput,
    Popen as StartProcess,
    TimeoutExpired as ChildTimeout,
)
from sys import executable as PythonExe


# coordinator failures must remain visible while application ownership stays with its native lifecycle
class FusionOwner:

    # the catalogue observes only the coordinator process and never owns its native descendants
    def __init__(OwnerState, ProcessValue, LogPath):
        OwnerState.Process = ProcessValue
        OwnerState.LogPath = LogPath

    # a stopped coordinator cannot perform the restart required by dependent native phases
    def CheckAlive(OwnerState):
        ExitValue = OwnerState.Process.poll()
        if ExitValue is not None:
            raise RuntimeError(
                f"Fusion lifecycle coordinator exited with code {ExitValue}; "
                f"inspect {OwnerState.LogPath}"
            )


# cleanup stops only the owned coordinator and preserves native processes and their recovery fences
def CloseOwner(OwnerState):
    ProcessValue = OwnerState.Process
    if ProcessValue.poll() is None:
        if OsName == "posix":
            ProcessValue.send_signal(KInterrupt)
        else:
            ProcessValue.terminate()
        try:
            ProcessValue.wait(timeout=10)
        except ChildTimeout:
            ProcessValue.terminate()
            try:
                ProcessValue.wait(timeout=10)
            except ChildTimeout:
                ProcessValue.kill()
                ProcessValue.wait(timeout=10)


# each catalogue must publish restart receipts to the coordinator that watches its own directory
@ContextManager
def OwnFusionLife(
    Directory, SourceRoot, ConfigPath, InstallationPath, LifecyclePath, Resume=False
):
    Directory = FilePath(Directory).resolve(strict=True)
    SourceRoot = FilePath(SourceRoot).resolve(strict=True)
    ScriptPath = SourceRoot / "re/automation/ApplicationWorkers/FusionLifecycleOwner.py"
    if ScriptPath.is_symlink() or not ScriptPath.is_file():
        raise ValueError("Fusion lifecycle coordinator must be a regular source file")
    if not ScriptPath.resolve(strict=True).is_relative_to(SourceRoot):
        raise ValueError("Fusion lifecycle coordinator escapes the source checkout")
    InputPaths = []
    for InputPath in (ConfigPath, InstallationPath, LifecyclePath):
        InputPath = FilePath(InputPath)
        if (
            not InputPath.is_absolute()
            or InputPath.is_symlink()
            or not InputPath.is_file()
        ):
            raise ValueError("Fusion lifecycle settings require regular absolute files")
        InputPaths.append(str(InputPath.resolve(strict=True)))
    CommandArgs = [
        PythonExe,
        "-B",
        str(ScriptPath),
        "--config",
        InputPaths[0],
        "--installation",
        InputPaths[1],
        "--lifecycle",
        InputPaths[2],
        "--queue-directory",
        str(Directory),
    ]
    LaunchOptions = {}
    if OsName == "nt":
        from subprocess import CREATE_NO_WINDOW as KHideWindow

        LaunchOptions["creationflags"] = KHideWindow
    LogPath = Directory / "FusionLifecycle.log"
    with LogPath.open("ab" if Resume else "xb") as LogStream:
        ProcessValue = StartProcess(
            CommandArgs,
            cwd=SourceRoot,
            stdin=KNullInput,
            stdout=LogStream,
            stderr=LogStream,
            **LaunchOptions,
        )
        OwnerState = FusionOwner(ProcessValue, LogPath)
        try:
            try:
                ProcessValue.wait(timeout=0.25)
            except ChildTimeout:
                pass
            OwnerState.CheckAlive()
            yield OwnerState
            OwnerState.CheckAlive()
        finally:
            CloseOwner(OwnerState)
