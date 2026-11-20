# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.SupervisorClient import KRepoRoot


# disposable source copies let guards reject changed dependencies while preserving every shared checkout byte
def PrepareSource(TmpPath: FilePath, Manifest: list[dict]) -> FilePath:
    SourceRoot = TmpPath / "SourceCopy"
    SourceRoot.mkdir()
    GitPath = RunProcess(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    _ = (SourceRoot / ".git").write_text("gitdir: " + GitPath + "\n", encoding="utf-8")
    for Entry in Manifest:
        Relative = FilePath(Entry["path"])
        if Relative.is_absolute() or ".." in Relative.parts:
            raise ValueError("unsafe source manifest path")
        Destination = SourceRoot / Relative
        Destination.parent.mkdir(parents=True, exist_ok=True)
        _ = Destination.write_bytes((KRepoRoot / Relative).read_bytes())
    return SourceRoot
