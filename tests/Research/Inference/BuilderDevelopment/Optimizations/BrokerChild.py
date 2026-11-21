# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import partial as BindCall
from collections.abc import Callable
from typing import cast as TypeCast
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from sys import argv as CliArgs, executable as PythonExe, path as SearchPaths
from sys import stdin as InputStream

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadConfig,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.FactoryTypes import (
    BrokerMaker,
    LiveProbe,
    SessionMaker as SessionFactoryType,
)


# a separate controller process exercises the real authenticated broker and provider process lifecycle
def MainBroker() -> None:
    ConfigValue = ReadConfig(FilePath(CliArgs[1]).read_text(encoding="utf-8"))
    RepoRoot = FilePath(__file__).resolve().parents[5]
    SourceRoot = FilePath(ConfigValue["source_root"])
    SearchPaths[:0] = [
        str(SourceRoot / "re/automation"),
        str(RepoRoot / "re/automation"),
        str(RepoRoot),
    ]
    AdviceOptions = TypeCast(
        Callable[[str, str, str | None, int], object],
        LoadSymbol("CodexAdvice.AdviceOptions", "AdviceOptions"),
    )
    GenerationBroker = TypeCast(
        BrokerMaker,
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.GenerationBroker",
            "GenerationBroker",
        ),
    )
    CodexSession = TypeCast(
        SessionFactoryType,
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession",
            "CodexSession",
        ),
    )
    ProcessStart = TypeCast(LiveProbe, LoadSymbol("Processes", "process_start"))

    ProcessEnv["PYTHONPATH"] = str(RepoRoot)
    FixturePath = (
        RepoRoot
        / "tests/Research/Inference/BuilderDevelopment/Transport/FixtureServer.py"
    )
    SessionMaker = BindCall(
        CodexSession,
        Command=[
            PythonExe,
            "-B",
            str(FixturePath),
            "delay",
            ConfigValue["provider_log"],
        ],
    )
    RunPath = FilePath(ConfigValue["run_root"])
    Broker = GenerationBroker(
        AdviceOptions("codex", "login", ConfigValue["model"], 3),
        RunPath,
        SessionMaker,
    )
    with Broker:
        _ = (RunPath / "BrokerReady.json").write_text("{}", encoding="utf-8")
        _ = InputStream.readline()
    SessionValue: object = getattr(Broker, "session")
    if SessionValue is not None:
        ProcessValue: object = getattr(SessionValue, "process")
        OwnerValue: object = getattr(ProcessValue, "owner")
        ChildValue: object = getattr(OwnerValue, "process")
        ServerPid: object = getattr(ChildValue, "pid")
        assert isinstance(ServerPid, int)
        assert ProcessStart(ServerPid, live=True) is None
    _ = (RunPath / "BrokerClosed.json").write_text("{}", encoding="utf-8")
