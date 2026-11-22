# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from shutil import copytree as CopyTree
from tests.Research.SupervisorClient import KRepoRoot


# a private source copy verifies code invalidation without changing the checkout under concurrent tests
def CopyChanged(TmpPath: FilePath, ChangeKind: str) -> FilePath:
    SourceRoot = TmpPath / "ChangedSource"
    GenFolder = "re/automation/InferenceGrid/BuilderDevelopment/Generation"
    _ = CopyTree(KRepoRoot / GenFolder, SourceRoot / GenFolder)
    SourcePath = (
        SourceRoot
        / GenFolder
        / ("GenerationPacket.py" if ChangeKind == "source" else "ProgramSchema.py")
    )
    SourceText = SourcePath.read_text(encoding="utf-8")
    if ChangeKind == "source":
        SourceText += "\n"
    else:
        SourceText = SourceText.replace(
            '"additionalProperties": False,',
            '"title": "fixture alternate schema", "additionalProperties": False,',
            1,
        )
    _ = SourcePath.write_text(SourceText, encoding="utf-8")
    return SourceRoot
