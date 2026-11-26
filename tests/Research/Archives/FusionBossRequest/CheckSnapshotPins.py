# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.SnapshotPins import KSnapshotPins


# receipt metadata must identify both exact helpers from the actual source free process
def CheckSnapPins(MirrorRoot: FilePath, HelperPins: object) -> None:
    Expected = {}
    for RoleValue, (
        LeafName,
        SourcePath,
        BlobId,
        ExpectedHash,
    ) in KSnapshotPins.items():
        HelperPath = (MirrorRoot / LeafName).resolve(strict=True)
        assert HashBytes(HelperPath.read_bytes()).hexdigest() == ExpectedHash
        Expected[RoleValue] = {
            "path": SourcePath,
            "revision": "a0c6e9f22082c7e0937f02af4464a1c06df9ed65",
            "git_blob": BlobId,
            "sha256": ExpectedHash,
            "import_origin": str(HelperPath),
        }
    assert HelperPins == Expected
