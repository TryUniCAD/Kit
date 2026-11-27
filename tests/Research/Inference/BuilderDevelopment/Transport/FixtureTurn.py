# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from json import dumps as EncodeJson
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from os import write as WriteBytes
from time import sleep as WaitBriefly
from tests.Research.Inference.BuilderDevelopment.Transport.FixtureReply import SendReply


# independent failure modes exercise real framing deadlines and capability rejection at the process boundary
def SendTurn(
    Request: Mapping[str, object], ModeName: str, ThreadId: str, ThreadCount: int
) -> None:
    assert ReadRecord(Request["params"])["effort"] == "low"
    TurnId = f"fixture-turn-{ThreadCount}"
    SendReply({"id": Request["id"], "result": {"turn": {"id": TurnId}}})
    if ModeName == "timeout":
        WaitBriefly(60)
    if ModeName == "delay":
        WaitBriefly(0.4)
    if ModeName == "oversized":
        for _ in range(80):
            _ = WriteBytes(1, b"x" * 65536)
    if ModeName == "tools":
        SendReply(
            {
                "id": 999,
                "method": "item/commandExecution/requestApproval",
                "params": {"threadId": ThreadId},
            }
        )
        return
    Candidate = {
        "schema": 1,
        "operation": "offset_plane",
        "support": "XY",
        "scale": 1,
        "reverse": False,
    }
    SendReply(
        {
            "method": "item/completed",
            "params": {
                "threadId": ThreadId,
                "turnId": TurnId,
                "item": {"type": "agentMessage", "text": EncodeJson(Candidate)},
            },
        }
    )
    SendReply(
        {
            "method": "thread/tokenUsage/updated",
            "params": {
                "threadId": ThreadId,
                "turnId": TurnId,
                "tokenUsage": {
                    "last": {
                        "inputTokens": 120,
                        "outputTokens": 32,
                        "cachedInputTokens": 0,
                        "totalTokens": 152,
                        "reasoningOutputTokens": 0,
                    }
                },
            },
        }
    )
    SendReply(
        {
            "method": "turn/completed",
            "params": {
                "threadId": ThreadId,
                "turn": {"id": TurnId, "status": "completed", "error": None},
            },
        }
    )
    return
