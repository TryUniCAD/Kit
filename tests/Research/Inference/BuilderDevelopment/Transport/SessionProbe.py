# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as ProcessEnv
from pathlib import Path as FilePath
from sys import argv as CliArgs, executable as PythonExe, path as SearchPaths
from threading import Thread as WorkerThread
from time import monotonic as MonoTime, sleep as WaitBriefly

# absolute roots let the protocol fixture import its independently executed handlers
KRepoRoot = FilePath(__file__).resolve().parents[5]

# process fixtures need the same checkout identity as their imported protocol client
SearchPaths[:0] = [str(KRepoRoot / "re/automation"), str(KRepoRoot)]

from CodexAdvice.AdviceOptions import AdviceOptions
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ProgramSchema
from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession import (
    CodexSession,
)
from tests.Research.Inference.BuilderDevelopment.Transport.ProbeReport import (
    WriteReport,
)


# a process boundary verifies provider isolation cancellation evidence and reuse without credentials
def MainProbe() -> None:
    ModeName, WorkPath = CliArgs[1], FilePath(CliArgs[2])
    FixturePath = FilePath(__file__).with_name("FixtureServer.py")
    ProcessEnv["PYTHONPATH"] = str(KRepoRoot)
    Session = CodexSession(
        AdviceOptions("codex", "login", "gpt-6.1-terra", 2),
        WorkPath / "Session",
        Command=[
            PythonExe,
            "-B",
            str(FixturePath),
            ModeName,
            str(WorkPath / "Calls.jsonl"),
        ],
        AllowPersonalInstructions=ModeName == "personalallowed",
    )
    Results = []
    StartedAt = MonoTime()
    try:
        if ModeName == "cancel":
            Session.command[-2] = "timeout"

            # cancellation must race a real request without changing its provider behavior
            Caller = WorkerThread(
                target=lambda: Results.append(
                    Session.Generate("first", ProgramSchema(), 10)
                )
            )
            Caller.start()
            WaitBriefly(0.3)
            Session.close()
            Caller.join(timeout=10)
            assert not Caller.is_alive()
        else:
            Results.append(
                Session.Generate(
                    "first", ProgramSchema(), 1 if ModeName == "timeout" else 10
                )
            )
            if ModeName in ("success", "descendant", "personalallowed"):
                Results.append(Session.Generate("second", ProgramSchema(), 10))
    finally:
        Session.close()
        Session.close()
    WriteReport(WorkPath, Session, Results, StartedAt)


if __name__ == "__main__":
    MainProbe()
