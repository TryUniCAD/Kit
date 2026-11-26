# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as DumpJson
from json import loads as ReadJson
from pathlib import Path as FilePath
from sys import platform as SysPlatform
from typing import cast as CastValue

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.RunExecution import (
    RunExecution,
)


# neither an offline plan nor a resealed label can authorize a native phase
def CheckExecGate(RepoPath: FilePath, PlanRoot: FilePath) -> None:
    if SysPlatform == "darwin":
        return
    PlanPath = (PlanRoot / "plan.json").resolve(strict=True)
    Original = PlanPath.read_bytes()
    OriginalSha, _ = ArtifactPin(PlanPath)
    RunExecution(
        RepoPath,
        PlanRoot,
        OriginalSha,
        "P03 native execution requires a plan resealed on the approved licensed macOS host",
    )
    Edited = CastValue(dict[str, object], ReadJson(Original))
    assert Edited["execution_paths"] is None
    Edited["preparation_host"] = "licensed_macos"
    try:
        _ = PlanPath.write_bytes(
            DumpJson(Edited, sort_keys=True, allow_nan=False).encode()
        )
        RunExecution(
            RepoPath, PlanRoot, OriginalSha, f"Witness JSON digest changed: {PlanPath}"
        )
        RunExecution(
            RepoPath,
            PlanRoot,
            ArtifactPin(PlanPath)[0],
            "P03 plan host and its execution binding disagree",
        )
    finally:
        _ = PlanPath.write_bytes(Original)
    assert PlanPath.read_bytes() == Original
    assert not (PlanRoot / "phase-a").exists() and not (PlanRoot / "phase-b").exists()
