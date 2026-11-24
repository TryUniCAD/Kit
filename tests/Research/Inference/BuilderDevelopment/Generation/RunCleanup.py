# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import dumps as EncodeJson, loads as DecodeJson
from os import environ as ProcessEnv
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from tests.Research.Inference.BuilderDevelopment.Contracts.LiveStart import LiveStart
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from sys import (
    argv as ArgValues,
    executable as PythonExe,
    path as ImportPaths,
    platform as PlatformName,
)
from tests.Research.SupervisorClient import KRepoRoot


# an independent harness checks real cleanup receipts without calling a model provider
def MainProbe() -> int:
    ImportPaths.insert(0, str(KRepoRoot / "re/automation"))
    RunProvider = CastValue(
        Callable[[list[str], FilePath, dict[str, str], int, int], dict[str, object]],
        ImportModule(
            "InferenceGrid.BuilderDevelopment.Generation.OwnedProviderProcess"
        ).RunProvider,
    )

    OutputPath = ResolveTemp(ArgValues[1])
    ModeName = ArgValues[2]
    _ = (OutputPath / "Prompt.txt").write_text("", encoding="utf-8")
    CommandArgs = [
        PythonExe,
        "-B",
        str(FilePath(__file__).with_name("ProviderChild.py")),
        ModeName,
    ]
    ResultInfo = RunProvider(CommandArgs, OutputPath, dict(ProcessEnv), 1, 256)
    LogText = (OutputPath / "Provider.jsonl").read_text(encoding="utf-8")
    ReceiptLines = LogText.splitlines()
    assert ModeName == "overflow" or ReceiptLines, "Provider did not publish a receipt"
    ChildInfo: dict[str, object] = (
        ReadRecord(DecodeJson(ReceiptLines[0])) if ModeName != "overflow" else {}
    )
    ChildPid = ChildInfo.get("child_pid")
    ChildStart = ChildInfo.get("child_start")
    if ModeName in {"descendant", "parentexit"}:
        assert isinstance(ChildPid, int)
        if PlatformName == "win32":
            assert isinstance(ChildStart, str)
    ResultInfo["child_still_live"] = isinstance(ChildPid, int) and (
        LiveStart(ChildPid) == ChildStart
        if PlatformName == "win32"
        else LiveStart(ChildPid) is not None
    )
    print(EncodeJson(ResultInfo), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainProbe())
