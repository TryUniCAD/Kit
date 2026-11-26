# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as DumpJson
from json import loads as ReadJson
from typing import cast as CastValue


# a new outer hash cannot make forged snapshot ownership or program pins valid
def ChangeManifest(Content: bytes, Change: str) -> bytes:
    Report = CastValue(dict[str, object], ReadJson(Content))
    if Change == "roles":
        Snapshot = CastValue(dict[str, object], Report["target_snapshot"])
        RootIds = CastValue(dict[str, int], Snapshot["root_ids"])
        RootIds["tool_solid"], RootIds["profile_region"] = (
            RootIds["profile_region"],
            RootIds["tool_solid"],
        )
    else:
        Generators = CastValue(dict[str, str], Report["generator_sources"])
        assert "SourceBossSnapshot.py" in Generators
        Generators["SourceBossSnapshot.py"] = "0" * 64
    return (
        DumpJson(
            Report,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
