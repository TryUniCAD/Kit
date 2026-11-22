# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from time import monotonic as MonoTime, sleep as WaitBriefly
from tests.Research.Inference.BuilderDevelopment.Contracts.LiveStart import LiveStart
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord


# independently observed process identities prove final cleanup before publishing the protocol receipt
def WriteReport(
    WorkPath: FilePath,
    Session: object,
    Results: list[dict[str, object]],
    StartedAt: float,
) -> None:
    ServerPid: object = getattr(
        getattr(getattr(Session, "process"), "owner"), "process"
    ).pid
    assert isinstance(ServerPid, int)
    Deadline = MonoTime() + 3
    while LiveStart(ServerPid) and MonoTime() < Deadline:
        WaitBriefly(0.02)
    assert LiveStart(ServerPid) is None
    Children = [
        ReadRecord(DecodeJson(LogLine))["descendant"]
        for LogLine in ResolveTemp(WorkPath / "Calls.jsonl").read_text().splitlines()
        if "descendant" in ReadRecord(DecodeJson(LogLine))
    ]
    for ChildPid in Children:
        assert isinstance(ChildPid, int)
        assert LiveStart(ChildPid) is None
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
