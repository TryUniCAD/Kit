# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.Archives.FusionBossRequest.SnapshotPins import KSnapshotPins


# the replay mirror needs trusted executable schema rules without the source archive
def CopySnapshot(SourceRoot: FilePath, MirrorRoot: FilePath) -> None:
    for LeafName, SourcePath, BlobId, ExpectedHash in KSnapshotPins.values():
        GitSpec = f"a0c6e9f22082c7e0937f02af4464a1c06df9ed65:{SourcePath}"
        Identity = (
            RunProcess(
                ["git", "rev-parse", GitSpec],
                cwd=SourceRoot,
                capture_output=True,
                check=True,
                timeout=30,
            )
            .stdout.decode("ascii")
            .strip()
        )
        assert Identity == BlobId
        Payload = RunProcess(
            ["git", "cat-file", "blob", BlobId],
            cwd=SourceRoot,
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        assert HashBytes(Payload).hexdigest() == ExpectedHash
        _ = (MirrorRoot / LeafName).write_bytes(Payload)
