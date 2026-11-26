# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.Research.Archives.FusionBossRequest.NativeWitness.RunWitness import (
    RunWitness,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)


# the operator supplies independent input digests before preparation can publish evidence
def RunPrepare(
    RepoPath: FilePath,
    Candidate: FilePath,
    OutputPath: FilePath,
    Inputs: dict[str, FilePath],
    ArchiveHash: str,
    ManifestHash: str,
) -> CompletedProcess[str]:
    ArgsValue = [
        "prepare-replay",
        "--candidate",
        str(Candidate),
        "--output",
        str(OutputPath),
        "--manifest-sha256",
        ManifestHash,
        "--archive-sha256",
        ArchiveHash,
        "--fusion-version",
        "2706.1.17",
    ]
    for RoleValue, PathValue in Inputs.items():
        FlagValue = (
            "--source-witness"
            if RoleValue == "witness"
            else "--" + RoleValue.replace("_", "-")
        )
        ArgsValue.extend((FlagValue, str(PathValue)))
        if RoleValue in ("request", "witness"):
            ArgsValue.extend((FlagValue + "-sha256", ArtifactPin(PathValue)[0]))
    return RunWitness(RepoPath, OutputPath.parent, *ArgsValue)
