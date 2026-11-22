# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from os import fspath
from pathlib import Path
from stat import FILE_ATTRIBUTE_REPARSE_POINT, S_ISLNK


# original path components are checked before resolution can hide a symlink or junction
def CheckComponents(Value):
    Original = Path(fspath(Value))
    if ".." in Original.parts:
        raise ValueError("generation paths must not contain parent traversal")
    Absolute = Original.absolute()
    for Part in reversed((Absolute, *Absolute.parents)):
        try:
            Status = Part.lstat()
        except FileNotFoundError:
            continue
        if (
            S_ISLNK(Status.st_mode)
            or getattr(Status, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError(
                "generation paths must not traverse symlinks or reparse points"
            )
    return Absolute


# attempts and accounting stay within the explicit existing private run directory supplied by the controller
def OwnedPath(Value, RunRoot):
    Root = CheckComponents(RunRoot)
    if not Root.is_dir():
        raise ValueError(
            "generation run_root must name an existing owned run directory"
        )
    Target = CheckComponents(Value)
    if not Target.is_relative_to(Root):
        raise ValueError("generation path escapes its owned run_root")
    ResolvedRoot, Resolved = Root.resolve(), Target.resolve()
    if not Resolved.is_relative_to(ResolvedRoot):
        raise ValueError("resolved generation path escapes its owned run_root")
    return Resolved


# hashing remains bounded in memory even after an interrupted or oversized provider response
def ArtifactHash(PathValue, RunRoot):
    Target = OwnedPath(PathValue, RunRoot)
    Hash, Size = sha256(), 0
    with Target.open("rb") as Source:
        while Chunk := Source.read(64 * 1024):
            Hash.update(Chunk)
            Size += len(Chunk)
    return {"path": str(Target), "sha256": Hash.hexdigest(), "size_bytes": Size}
