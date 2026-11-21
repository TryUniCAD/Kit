# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath


# fixture threads assert capability isolation before any simulated model response is emitted
def ThreadReply(Params: dict, ModeName: str, ThreadId: str) -> dict:
    assert Params["ephemeral"] is True
    assert Params["approvalPolicy"] == "never"
    assert Params["sandbox"] == "read-only"
    assert Params["developerInstructions"] == ""
    assert Params["config"]["project_doc_max_bytes"] == 0
    assert Params["config"]["mcp_servers"] == {}
    assert all(
        Value is False
        for FieldName, Value in Params["config"]["features"].items()
        if FieldName != "code_mode"
    )
    assert Params["config"]["features"]["code_mode"]["enabled"] is False
    assert Params["config"]["skills"]["include_instructions"] is False
    assert len(Params["baseInstructions"]) < 1000
    return {
        "thread": {"id": ThreadId},
        "model": "wrong-model" if ModeName == "wrongmodel" else Params["model"],
        "approvalPolicy": "never",
        "sandbox": {"type": "readOnly"},
        "instructionSources": (
            [str(FilePath.home() / ".codex/AGENTS.md")]
            if ModeName in ("personal", "personalallowed")
            else []
        ),
    }
