# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from time import time as WallTime

from tests.Research.Windows.Readback.ReadbackProgram import KReadbackScript
from tests.Research.Windows.Readback.ProgressProgram import KProgressScript


# dispatch must consume an explicit operation and the same source snapshot as its listener
def PrepareReadback(
    TmpPath: FilePath, ConfigPath: FilePath, Operation: str
) -> FilePath:
    ProgramPath = TmpPath / "ReadbackHost.py"
    _ = ProgramPath.write_text(KReadbackScript, encoding="utf-8")
    _ = (TmpPath / "Progress.ps1").write_text(KProgressScript, encoding="utf-8")
    SessionPath = TmpPath / "Session"
    (SessionPath / "work").mkdir(parents=True)
    Revision = DecodeJson(ConfigPath.read_bytes())["source_revision"]
    _ = (SessionPath / "job.json").write_text(
        EncodeJson(
            {
                "session_version": 1,
                "inputs": {},
                "stop_at": WallTime() + 45,
                "job": {
                    "options": {
                        "source_revision": Revision,
                        "readback_operation": Operation,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return ProgramPath
