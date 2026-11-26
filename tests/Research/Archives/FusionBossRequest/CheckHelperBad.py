# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.ReplayBoss import ReplayBoss
from tests.Research.Archives.FusionBossRequest.SnapshotPins import KSnapshotPins


# replay must reject altered helper bytes before writing any candidate results
def CheckHelperBad(
    MirrorRoot: FilePath, PrepPath: FilePath, WorkPath: FilePath
) -> None:
    LeafName, SourcePath, _, _ = KSnapshotPins["builder"]
    Original = MirrorRoot / LeafName
    Expected = Original.read_bytes()
    Changed = MirrorRoot / "ChangedBuilder.py"
    Mutation = Expected + b"\n"
    _ = Changed.write_bytes(Mutation)
    OutputPath = WorkPath / "RejectedHelper"
    Result = ReplayBoss(
        MirrorRoot,
        PrepPath / "P03Request.json",
        PrepPath / "P03SourceWitness.json",
        OutputPath,
        Changed,
    )
    assert Result.returncode == 1
    assert (
        f"P03 helper differs from the pinned Git blob for {SourcePath}" in Result.stderr
    )
    assert not OutputPath.exists()
    assert Changed.read_bytes() == Mutation and Original.read_bytes() == Expected
