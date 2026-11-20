# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from zipfile import ZIP_STORED as KStoredZip, ZipFile as NativeBundle


# independent artifact roles need distinct archive rosters even when their retained control bytes match
def WriteBundle(
    SessionPath: FilePath, Label: str, Content: bytes, Fault: str
) -> tuple[dict, dict]:
    FileName = Label + ".f3d"
    BundlePath = SessionPath / "work" / (Label + ".zip")
    with NativeBundle(BundlePath, "x", compression=KStoredZip) as Bundle:
        Bundle.writestr(
            FileName, Content + b"tampered" if Fault == "tamper" else Content
        )
    Packed = BundlePath.read_bytes()
    Members = {
        FileName: {"sha256": HashBytes(Content).hexdigest(), "size_bytes": len(Content)}
    }
    Artifact = {
        "path": BundlePath.name,
        "sha256": HashBytes(Packed).hexdigest(),
        "size_bytes": len(Packed),
    }
    return Members, Artifact
