# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from shutil import copyfile as CopyFile


# replay must run from code and declared codec vocabulary without access to an archive checkout
def MirrorBossCode(SourceRoot: FilePath, MirrorRoot: FilePath) -> None:
    for Folder in (
        "src",
        "re/automation",
        "re/Fusion/Reconstruction/DimensionAuthoring",
        "re/Fusion/Study",
        "re/solidworks/WriterResearch",
    ):
        SourceFolder = SourceRoot / Folder
        assert SourceFolder.is_dir(), SourceFolder
        Suffixes = {".py", ".json", ".xz"} if Folder == "src" else {".py"}
        for CodePath in SourceFolder.rglob("*"):
            if CodePath.suffix.lower() not in Suffixes or not CodePath.is_file():
                continue
            TargetPath = MirrorRoot / CodePath.relative_to(SourceRoot)
            TargetPath.parent.mkdir(parents=True, exist_ok=True)
            _ = CopyFile(CodePath, TargetPath)
    assert not (MirrorRoot / ".git").exists()
