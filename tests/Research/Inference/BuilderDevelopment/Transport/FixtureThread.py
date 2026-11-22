# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from pathlib import Path as FilePath
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadText import ReadText


# fixture threads assert capability isolation before any simulated model response is emitted
def ThreadReply(
    Params: Mapping[str, object], ModeName: str, ThreadId: str
) -> dict[str, object]:
    ConfigValue = ReadRecord(Params["config"])
    Features = ReadRecord(ConfigValue["features"])
    assert Params["ephemeral"] is True
    assert Params["approvalPolicy"] == "never"
    assert Params["sandbox"] == "read-only"
    assert Params["developerInstructions"] == ""
    assert ConfigValue["project_doc_max_bytes"] == 0
    assert ConfigValue["mcp_servers"] == {}
    assert all(
        Value is False
        for FieldName, Value in Features.items()
        if FieldName != "code_mode"
    )
    assert ReadRecord(Features["code_mode"])["enabled"] is False
    assert ReadRecord(ConfigValue["skills"])["include_instructions"] is False
    assert len(ReadText(Params["baseInstructions"])) < 1000
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
