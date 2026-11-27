# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from json import dumps as EncodeJson
from typing import cast as TypeCast
from pathlib import Path as FilePath

from tests.Research.Inference.BuilderDevelopment.Optimizations.LoadSymbol import (
    LoadSymbol,
)


# changed endpoint evidence must fail before exposing the request to a different owner or instruction scope
def RejectRecord(
    RunPath: FilePath, Record: dict[str, object], ModelName: str, ModeName: str
) -> None:
    AdviceOptions = TypeCast(
        Callable[[str, str, str | None, int], object],
        LoadSymbol("CodexAdvice.AdviceOptions", "AdviceOptions"),
    )
    CallBroker = TypeCast(
        Callable[
            [object, str, dict[str, object], FilePath, dict[str, object], FilePath],
            dict[str, object],
        ],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.Broker.CallBroker",
            "CallBroker",
        ),
    )
    ProgramSchema = TypeCast(
        Callable[[], dict[str, object]],
        LoadSymbol(
            "InferenceGrid.BuilderDevelopment.Generation.ProgramSchema", "ProgramSchema"
        ),
    )

    ChangedValue = dict(Record)
    if ModeName == "remote":
        ChangedValue["host"] = "192.0.2.1"
    elif ModeName == "owner":
        ChangedValue["pid_start"] = "fixture mismatched process identity"
    elif ModeName == "instructions":
        ChangedValue["personal_instructions"] = True
    RecordPath = RunPath / "RejectedBroker.json"
    _ = RecordPath.write_text(
        EncodeJson([] if ModeName == "recordshape" else ChangedValue), encoding="utf-8"
    )
    try:
        _ = CallBroker(
            AdviceOptions("codex", "login", ModelName, 1),
            "fixture request",
            ProgramSchema(),
            RunPath / "Rejected",
            {"run_root": str(RunPath), "seconds": 1},
            RecordPath,
        )
    except (OSError, ValueError) as Error:
        print(EncodeJson({"error": str(Error)}), flush=True)
        return
    raise AssertionError("changed ownership record was accepted")
