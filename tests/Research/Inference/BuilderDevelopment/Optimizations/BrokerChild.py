# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import partial as BindCall
from json import loads as DecodeJson
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from sys import argv as CliArgs, executable as PythonExe, path as SearchPaths
from sys import stdin as InputStream


# a separate controller process exercises the real authenticated broker and provider process lifecycle
def MainBroker() -> None:
    ConfigValue = DecodeJson(FilePath(CliArgs[1]).read_text(encoding="utf-8"))
    RepoRoot = FilePath(__file__).resolve().parents[5]
    SourceRoot = FilePath(ConfigValue["source_root"])
    SearchPaths[:0] = [
        str(SourceRoot / "re/automation"),
        str(RepoRoot / "re/automation"),
        str(RepoRoot),
    ]
    from CodexAdvice.AdviceOptions import AdviceOptions
    from InferenceGrid.BuilderDevelopment.Generation.Broker.GenerationBroker import (
        GenerationBroker,
    )
    from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession import (
        CodexSession,
    )
    from Processes import process_start as ProcessStart

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
        SessionFactory=SessionMaker,
    )
    with Broker:
        _ = (RunPath / "BrokerReady.json").write_text("{}", encoding="utf-8")
        _ = InputStream.readline()
    if Broker.session is not None:
        ServerPid = Broker.session.process.owner.process.pid
        assert ProcessStart(ServerPid, live=True) is None
    _ = (RunPath / "BrokerClosed.json").write_text("{}", encoding="utf-8")
