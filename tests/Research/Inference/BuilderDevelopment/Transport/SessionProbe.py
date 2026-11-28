# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from os import environ as ProcessEnv
from pathlib import Path as FilePath
from sys import argv as CliArgs, path as SearchPaths
from threading import Thread as WorkerThread
from time import monotonic as MonoTime

# absolute roots let the protocol fixture import its independently executed handlers
KRepoRoot = FilePath(__file__).resolve().parents[5]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from tests.Research.Inference.BuilderDevelopment.Contracts.MakeSession import (
    MakeSession,
)
from tests.Research.Inference.BuilderDevelopment.Contracts.SessionHooks import (
    BindSession,
)
from tests.Research.Inference.BuilderDevelopment.Transport.WaitRequest import (
    WaitRequest,
)

from tests.Research.Inference.BuilderDevelopment.Transport.ProbeReport import (
    WriteReport,
)


# a process boundary verifies provider isolation cancellation evidence and reuse without credentials
def MainProbe() -> None:
    ModeName, WorkPath = CliArgs[1], FilePath(CliArgs[2])
    FixturePath = FilePath(__file__).with_name("FixtureServer.py")
    ProcessEnv["PYTHONPATH"] = str(KRepoRoot)
    ResolveTemp(WorkPath / "Calls.jsonl").touch(exist_ok=False)
    Session = MakeSession(WorkPath, FixturePath, ModeName)
    Hooks = BindSession(Session)
    SchemaMaker = CastValue(
        Callable[[], dict[str, object]],
        ImportModule(
            "InferenceGrid.BuilderDevelopment.Generation.ProgramSchema"
        ).ProgramSchema,
    )
    Results: list[dict[str, object]] = []
    StartedAt = MonoTime()
    try:
        if ModeName == "cancel":
            Hooks.CommandArgs[-2] = "timeout"
            RequestSeconds = 10

            # cancellation must race a real request without changing its provider behavior
            Caller = WorkerThread(
                target=lambda: Results.append(
                    Hooks.GenerateCall("first", SchemaMaker(), RequestSeconds)
                )
            )
            Caller.start()
            WaitRequest(Session, StartedAt + RequestSeconds)
            Hooks.CloseCall()
            Caller.join(timeout=10)
            assert not Caller.is_alive()
        else:
            Results.append(
                Hooks.GenerateCall(
                    "first", SchemaMaker(), 1 if ModeName == "timeout" else 10
                )
            )
            if ModeName in ("success", "descendant", "personalallowed"):
                Results.append(Hooks.GenerateCall("second", SchemaMaker(), 10))
    finally:
        Hooks.CloseCall()
        Hooks.CloseCall()
    WriteReport(WorkPath, Session, Results, StartedAt)


if __name__ == "__main__":
    MainProbe()
