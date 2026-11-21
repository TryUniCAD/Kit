# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import JSONDecodeError
from pathlib import Path as FilePath
from time import monotonic as MonoTime, sleep as WaitBriefly

from convert.Security.PathBoundary import ResolveTemp
from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    ReadRecord,
)


# cancellation must observe an active provider turn rather than depend on machine startup speed
def WaitRequest(WorkPath: FilePath) -> None:
    LogPath = ResolveTemp(WorkPath / "Calls.jsonl")
    Deadline = MonoTime() + 5
    while MonoTime() < Deadline:
        try:
            for LineText in LogPath.read_text(encoding="utf-8").splitlines():
                RequestValue = ReadRecord(LineText).get("request")
                if (
                    isinstance(RequestValue, dict)
                    and RequestValue.get("method") == "turn/start"
                ):
                    return
        except (FileNotFoundError, JSONDecodeError):
            pass
        WaitBriefly(0.01)
    raise AssertionError("provider turn did not start before cancellation deadline")
