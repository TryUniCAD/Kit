# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from re import fullmatch as MatchText
from tests.Research.Inference.Authoring.Contracts.ArtifactData import ArtifactData


# fixture transport must consume the immutable input selected by the actual controller
def ReadFixture(SessionPath: FilePath, Descriptor: ArtifactData) -> bytes:
    Digest = Descriptor["sha256"]
    if (
        not MatchText("[0-9a-f]{64}", Digest)
        or Descriptor["path"] != "inputs/" + Digest
    ):
        raise ValueError("invalid fixture source binding")
    Content = ResolveTemp(SessionPath / Descriptor["path"]).read_bytes()
    if len(Content) > 64 * 1024 * 1024 or HashBytes(Content).hexdigest() != Digest:
        raise ValueError("fixture source differs from its immutable input")
    return Content
