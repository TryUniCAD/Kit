# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp, ValidateLabel

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from zipfile import ZIP_STORED as KStoredZip, ZipFile as NativeBundle
from tests.Research.Inference.Authoring.Contracts.ArtifactData import (
    ArtifactData,
    MemberData,
)


# independent artifact roles need distinct archive rosters even when their retained control bytes match
def WriteBundle(
    SessionPath: FilePath, Label: str, Content: bytes, Fault: str
) -> tuple[dict[str, MemberData], ArtifactData]:
    FileName = Label + ".f3d"
    BundlePath = ResolveTemp(SessionPath / "work" / (ValidateLabel(Label) + ".zip"))
    with NativeBundle(BundlePath, "x", compression=KStoredZip) as Bundle:
        Bundle.writestr(
            FileName, Content + b"tampered" if Fault == "tamper" else Content
        )
    Packed = BundlePath.read_bytes()
    Members: dict[str, MemberData] = {
        FileName: {"sha256": HashBytes(Content).hexdigest(), "size_bytes": len(Content)}
    }
    Artifact: ArtifactData = {
        "path": BundlePath.name,
        "sha256": HashBytes(Packed).hexdigest(),
        "size_bytes": len(Packed),
    }
    return Members, Artifact
