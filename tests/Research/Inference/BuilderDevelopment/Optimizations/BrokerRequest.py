# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from collections.abc import Callable
from json import dumps as EncodeJson
from typing import cast as TypeCast
from pathlib import Path as FilePath
from sys import argv as CliArgs, path as SearchPaths
from time import monotonic as MonoTime

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadConfig,
    ReadRecord,
)
from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# independent peers exercise rejection before any provider request can be authorized
def MainRequest() -> None:
    ConfigValue = ReadConfig(ResolveTemp(CliArgs[1]).read_bytes())
    RepoRoot = FilePath(__file__).resolve().parents[5]
    SearchPaths[:0] = [str(RepoRoot / "re/automation"), str(RepoRoot)]
    ProgramSchema = TypeCast(
        Callable[[], dict[str, object]],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.ProgramSchema", "ProgramSchema"
        ),
    )
    from tests.Research.Inference.BuilderDevelopment.Optimizations.RejectedRecord import (
        RejectRecord,
    )
    from tests.Research.Inference.BuilderDevelopment.Optimizations.QueueRequest import (
        RejectQueued,
    )
    from tests.Research.Inference.BuilderDevelopment.Optimizations.RejectedPeer import (
        RejectPeer,
    )

    RunPath = FilePath(ConfigValue["run_root"])
    ModeName = ConfigValue["action"]
    Record = ReadRecord((RunPath / "ProviderBroker.json").read_bytes())
    StartedAt = MonoTime()
    if ModeName in {"remote", "owner", "recordshape", "instructions"}:
        RejectRecord(RunPath, Record, ConfigValue["model"], ModeName)
        return
    SchemaValue = ProgramSchema()
    if ModeName == "schema":
        SchemaValue["title"] = "fixture wrong schema"
    RequestValue: dict[str, object] = {
        "provider": "codex",
        "auth": "login",
        "model": ConfigValue["model"],
        "prompt": "fixture request",
        "schema": SchemaValue,
        "seconds": 2,
        "deadline": MonoTime() + 2,
    }
    if ModeName == "queued":
        RejectQueued(Record, RequestValue)
        return
    Reply = RejectPeer(Record, RequestValue, ModeName)
    assert "error" in Reply, Reply
    print(
        EncodeJson({"error": Reply["error"], "seconds": MonoTime() - StartedAt}),
        flush=True,
    )
