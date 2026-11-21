# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath


# changed endpoint evidence must fail before exposing the request to a different owner or instruction scope
def RejectRecord(
    RunPath: FilePath, Record: dict, ModelName: str, ModeName: str
) -> None:
    from CodexAdvice.AdviceOptions import AdviceOptions
    from InferenceGrid.BuilderDevelopment.Generation.Broker.CallBroker import CallBroker
    from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ProgramSchema

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
        CallBroker(
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
