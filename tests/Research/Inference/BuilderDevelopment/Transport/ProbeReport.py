# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from time import monotonic as MonoTime, sleep as WaitBriefly
from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexSession import (
    CodexSession,
)
from Processes import process_start as ProcessStart


# independently observed process identities prove final cleanup before publishing the protocol receipt
def WriteReport(
    WorkPath: FilePath, Session: CodexSession, Results: list, StartedAt: float
) -> None:
    ServerPid = Session.process.owner.process.pid
    Deadline = MonoTime() + 3
    while ProcessStart(ServerPid, live=True) and MonoTime() < Deadline:
        WaitBriefly(0.02)
    assert ProcessStart(ServerPid, live=True) is None
    Children = [
        DecodeJson(LogLine)["descendant"]
        for LogLine in (WorkPath / "Calls.jsonl").read_text().splitlines()
        if "descendant" in DecodeJson(LogLine)
    ]
    for ChildPid in Children:
        assert ProcessStart(ChildPid, live=True) is None
    print(
        EncodeJson(
            {
                "results": Results,
                "elapsed_seconds": MonoTime() - StartedAt,
                "server_pid": ServerPid,
                "owned_tree_closed": True,
            }
        ),
        flush=True,
    )
