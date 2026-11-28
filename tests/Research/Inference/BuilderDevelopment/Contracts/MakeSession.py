# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule
from pathlib import Path as FilePath
from sys import executable as PythonExe
from typing import Callable, cast as CastValue
from tests.Research.Inference.BuilderDevelopment.Contracts.SessionMaker import (
    SessionMaker,
)


# exact constructor contracts keep fixture transport and model policy on the real research client
def MakeSession(WorkPath: FilePath, FixturePath: FilePath, ModeName: str) -> object:
    OptionsMaker = CastValue(
        Callable[[str, str, str, int], object],
        ImportModule("CodexAdvice.AdviceOptions").AdviceOptions,
    )
    SessionBuild = CastValue(
        SessionMaker,
        ImportModule(
            "InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession"
        ).CodexSession,
    )
    return SessionBuild(
        OptionsMaker("codex", "login", "gpt-6.1-terra", 2),
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
