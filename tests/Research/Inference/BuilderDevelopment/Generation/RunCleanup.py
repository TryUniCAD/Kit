# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from sys import argv as ArgValues, executable as PythonExe, path as ImportPaths
from tests.Research.SupervisorClient import KRepoRoot


# an independent harness checks real cleanup receipts without calling a model provider
def MainProbe() -> int:
    ImportPaths.insert(0, str(KRepoRoot / "re/automation"))
    from InferenceGrid.BuilderDevelopment.Generation.OwnedProviderProcess import (
        RunProvider,
    )
    from Processes import process_start as ProcessStart

    OutputPath = FilePath(ArgValues[1])
    ModeName = ArgValues[2]
    (OutputPath / "Prompt.txt").write_text("", encoding="utf-8")
    CommandArgs = [
        PythonExe,
        "-B",
        str(FilePath(__file__).with_name("ProviderChild.py")),
        ModeName,
    ]
    ResultInfo = RunProvider(CommandArgs, OutputPath, dict(ProcessEnv), 1, Limit=256)
    LogText = (OutputPath / "Provider.jsonl").read_text(encoding="utf-8")
    ChildInfo = DecodeJson(LogText.splitlines()[0]) if ModeName != "overflow" else {}
    ChildPid = ChildInfo.get("child_pid")
    ResultInfo["child_still_live"] = (
        ChildPid is not None and ProcessStart(ChildPid, live=True) is not None
    )
    print(EncodeJson(ResultInfo), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainProbe())
