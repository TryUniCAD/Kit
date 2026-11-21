# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import argv as CliArgs, path as SearchPaths, stdin as InputStream


# independent workers must cross real file locks and sockets before reusing a generation result
def MainWorker() -> None:
    ConfigValue = DecodeJson(FilePath(CliArgs[1]).read_text(encoding="utf-8"))
    RepoRoot = FilePath(__file__).resolve().parents[5]
    SourceRoot = FilePath(ConfigValue["source_root"])
    SearchPaths[:0] = [
        str(SourceRoot / "re/automation"),
        str(RepoRoot / "re/automation"),
        str(RepoRoot),
    ]
    from CodexAdvice.AdviceOptions import AdviceOptions
    from InferenceGrid.BuilderDevelopment.Generation.Cache.RequestCache import (
        RequestCache,
    )
    from InferenceGrid.BuilderDevelopment.Generation.GenerateCandidate import (
        GenerateCandidate,
    )
    from InferenceGrid.BuilderDevelopment.Generation.GenerationPacket import (
        GenerationPacket,
    )
    from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ProgramSchema

    RunPath = FilePath(ConfigValue["run_root"])
    PacketValue = DecodeJson(FilePath(ConfigValue["packet_path"]).read_bytes())
    ModelOpts = AdviceOptions("codex", "login", ConfigValue["model"], 3)
    BudgetValue = {
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
    ResultValue = GenerateCandidate(
        PacketValue,
        ModelOpts,
        RunPath / ConfigValue["attempt"],
        BudgetValue,
    )
    print(EncodeJson(ResultValue), flush=True)
    raise SystemExit(0 if ResultValue["status"] == "candidate" else 3)
