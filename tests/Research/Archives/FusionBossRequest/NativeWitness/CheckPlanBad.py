# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.NativeWitness.RunPrepare import (
    RunPrepare,
)


# failed preparation cannot publish partial evidence or modify an occupied directory
def CheckPlanBad(
    RepoPath: FilePath,
    Candidate: FilePath,
    WorkPath: FilePath,
    Inputs: dict[str, FilePath],
    ArchiveHash: str,
    ManifestHash: str,
) -> None:
    Helper = Inputs["snapshot_builder"]
    Original = Helper.read_bytes()
    Altered = WorkPath / "AlteredHelper"
    Altered.mkdir()
    Changed = Altered / Helper.name
    _ = Changed.write_bytes(Original + b"\n")
    Rejected = WorkPath / "RefusedHelper"
    Result = RunPrepare(
        RepoPath,
        Candidate,
        Rejected,
        {**Inputs, "snapshot_builder": Changed},
        ArchiveHash,
        ManifestHash,
    )
    assert (
        Result.returncode != 0
        and "P03 replay snapshot_builder digest differs" in Result.stderr
    ), Result.stderr
    assert not Rejected.exists() and Helper.read_bytes() == Original
    assert Changed.read_bytes() == Original + b"\n"
    Occupied = WorkPath / "OccupiedWitness"
    Occupied.mkdir()
    Sentinel = Occupied / "Sentinel"
    _ = Sentinel.write_bytes(b"existing witness destination")
    Result = RunPrepare(
        RepoPath, Candidate, Occupied, Inputs, ArchiveHash, ManifestHash
    )
    assert (
        Result.returncode != 0 and "new private witness directory" in Result.stderr
    ), Result.stderr
    assert list(Occupied.iterdir()) == [Sentinel]
    assert Sentinel.read_bytes() == b"existing witness destination"
