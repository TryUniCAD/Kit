# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.Research.Archives.FusionBossRequest.RunBossProbe import RunBossProbe


# the replay command must validate separate retained digests before materializing output
def ReplayBoss(
    MirrorRoot: FilePath, Request: FilePath, Witness: FilePath, OutputPath: FilePath
) -> CompletedProcess[str]:
    return RunBossProbe(
        MirrorRoot,
        MirrorRoot,
        "--request",
        str(Request),
        "--request-sha256",
        HashBytes(Request.read_bytes()).hexdigest(),
        "--source-witness",
        str(Witness),
        "--source-witness-sha256",
        HashBytes(Witness.read_bytes()).hexdigest(),
        "--seed-helper",
        str(MirrorRoot / "SeedHelper.py"),
        "--written-at",
        "1735689600",
        "--output",
        str(OutputPath),
    )
