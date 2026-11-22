# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from re import fullmatch

from Corpus import git
from InferenceGrid.Authoring.NativeSources import SolidSourceSet


# source receipts must identify every reviewed native dependency at the scheduled immutable revision
def ReadSolidPins(Revision, SourceRoot=None):
    if not isinstance(Revision, str) or fullmatch("[0-9a-f]{40}", Revision) is None:
        raise ValueError("SOLIDWORKS authoring requires an immutable source revision")
    SourceRoot = (
        Path(__file__).resolve().parents[4]
        if SourceRoot is None
        else Path(SourceRoot).resolve(strict=True)
    )
    Manifest = []
    for Relative in SolidSourceSet(SourceRoot, Revision):
        SourcePath = SourceRoot / Relative
        if (
            not SourcePath.is_file()
            or SourcePath.is_symlink()
            or any(
                Parent.is_symlink()
                for Parent in SourcePath.parents
                if Parent.is_relative_to(SourceRoot)
            )
            or not SourcePath.resolve(strict=True).is_relative_to(SourceRoot)
        ):
            raise ValueError(
                "SOLIDWORKS authoring source is missing or escapes its checkout"
            )
        Content = SourcePath.read_bytes()
        if Content != git(SourceRoot, "show", Revision + ":" + Relative):
            raise ValueError(
                "SOLIDWORKS authoring source differs from its scheduled revision"
            )
        Manifest.append(
            {
                "path": Relative,
                "sha256": sha256(Content).hexdigest(),
                "size_bytes": len(Content),
            }
        )
    return Manifest


# native startup must reject any dependency changed after the controller scheduled its recipe
def CheckSolidSrc(Revision, SourceRoot=None):
    ReadSolidPins(Revision, SourceRoot)
