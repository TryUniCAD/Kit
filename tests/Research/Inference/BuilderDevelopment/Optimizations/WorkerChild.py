# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from collections.abc import Callable
from contextlib import AbstractContextManager as ContextScope
from json import dumps as EncodeJson
from typing import cast as TypeCast
from pathlib import Path as FilePath
from sys import argv as CliArgs, path as SearchPaths, stdin as InputStream

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadConfig,
    ReadRecord,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# independent workers must cross real file locks and sockets before reusing a generation result
def MainWorker() -> None:
    ConfigValue = ReadConfig(ResolveTemp(CliArgs[1]).read_text(encoding="utf-8"))
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
    RequestCache = TypeCast(
        Callable[
            [dict[str, object], str, object, dict[str, object]], ContextScope[object]
        ],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Cache.RequestCache",
            "RequestCache",
        ),
    )
    GenerateCandidate = TypeCast(
        Callable[
            [dict[str, object], object, FilePath, dict[str, object]], dict[str, object]
        ],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.GenerateCandidate",
            "GenerateCandidate",
        ),
    )
    GenerationPacket = TypeCast(
        Callable[[dict[str, object]], tuple[dict[str, object], str]],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.GenerationPacket",
            "GenerationPacket",
        ),
    )
    ProgramSchema = TypeCast(
        Callable[[], dict[str, object]],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.ProgramSchema", "ProgramSchema"
        ),
    )

    RunPath = FilePath(ConfigValue["run_root"])
    PacketValue = ReadRecord(FilePath(ConfigValue["packet_path"]).read_bytes())
    ModelOpts = AdviceOptions("codex", "login", ConfigValue["model"], 3)
    BudgetValue: dict[str, object] = {
        "authorized": True,
        "run_root": str(RunPath),
        "state_path": str(RunPath / "ModelBudget.json"),
        "shared_root": ConfigValue["shared_root"],
        "broker_path": str(RunPath / "ProviderBroker.json"),
        "max_calls": 3,
        "call_seconds": 8,
        "max_seconds": 15,
    }
    if ConfigValue["action"] == "hold":
        _, PacketPin = GenerationPacket(PacketValue)
        with RequestCache(BudgetValue, PacketPin, ModelOpts, ProgramSchema()):
            _ = (RunPath / "OwnerReady.json").write_text("{}", encoding="utf-8")
            _ = InputStream.readline()
        return
    _ = (RunPath / (ConfigValue["attempt"] + ".Ready.json")).write_text(
        "{}", encoding="utf-8"
    )
    ResultValue = GenerateCandidate(
        PacketValue,
        ModelOpts,
        RunPath / ConfigValue["attempt"],
        BudgetValue,
    )
    print(EncodeJson(ResultValue), flush=True)
    raise SystemExit(0 if ResultValue["status"] == "candidate" else 3)
