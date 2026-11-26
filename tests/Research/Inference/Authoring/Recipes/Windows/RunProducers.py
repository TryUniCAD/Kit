# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import PIPE as KPipeValue, Popen as ChildProcess
from sys import executable as PythonExe
from time import monotonic as ReadClock, sleep as SleepBriefly

from tests.Research.SupervisorClient import KRepoRoot


# a real process barrier exposes simultaneous publication races without substituting filesystem behavior
def RunProducers(
    TmpPath: FilePath, StorePath: FilePath, InputPath: FilePath
) -> list[dict[str, object]]:
    ReleasePath = TmpPath / "Release.signal"
    ReadyPaths = [
        TmpPath / (Label + ".signal")
        for Label in ("First", "Second", "Third", "Fourth")
    ]
    Processes: list[ChildProcess[str]] = []
    try:
        for ReadyPath in ReadyPaths:
            Processes.append(
                ChildProcess(
                    [
                        PythonExe,
                        "-B",
                        str(FilePath(__file__).with_name("ArtifactProducer.py")),
                        str(StorePath),
                        str(InputPath),
                        str(ReadyPath),
                        str(ReleasePath),
                    ],
                    cwd=KRepoRoot,
                    stdout=KPipeValue,
                    stderr=KPipeValue,
                    text=True,
                )
            )
        Deadline = ReadClock() + 20
        while not all(ReadyPath.is_file() for ReadyPath in ReadyPaths):
            if (
                any(Process.poll() is not None for Process in Processes)
                or ReadClock() >= Deadline
            ):
                raise RuntimeError(
                    "artifact producers failed before their publication barrier"
                )
            SleepBriefly(0.01)
        ReleasePath.touch(exist_ok=False)
        Results: list[dict[str, object]] = []
        for Process in Processes:
            Output, Errors = Process.communicate(timeout=30)
            assert Process.returncode == 0, Output + Errors
            Results.append(DecodeJson(Output))
        return Results
    finally:
        for Process in Processes:
            if Process.poll() is None:
                Process.terminate()
            _ = Process.communicate(timeout=5)
