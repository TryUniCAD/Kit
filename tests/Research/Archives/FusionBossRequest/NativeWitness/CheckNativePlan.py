# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.CheckInspection import (
    CheckInspection,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.CheckPlanBad import (
    CheckPlanBad,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.CheckPlanFiles import (
    CheckPlanFiles,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.CheckPlanStage import (
    CheckPlanStage,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.CheckSourceBad import (
    CheckSourceBad,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.RunPrepare import (
    RunPrepare,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.WitnessInputs import (
    WitnessInputs,
)


# the handoff should accept only proved replay bytes before any licensed phase runs
def CheckNativePlan(
    RepoPath: FilePath,
    WorkPath: FilePath,
    Candidate: FilePath,
    PrepPath: FilePath,
    MirrorRoot: FilePath,
) -> None:
    Inputs = WitnessInputs(PrepPath, MirrorRoot)
    Before = {
        RoleValue: ArtifactPin(FileValue) for RoleValue, FileValue in Inputs.items()
    }
    ArchiveHash, _ = ArtifactPin(Candidate / "P03-baseline-a.f3d")
    ManifestHash, _ = ArtifactPin(Candidate / "P03CandidateEvidence.json")
    PlanRoot = WorkPath / "NativePlan"
    Result = RunPrepare(
        RepoPath, Candidate, PlanRoot, Inputs, ArchiveHash, ManifestHash
    )
    PlanData = CheckPlanStage(PlanRoot, Result)
    CheckPlanFiles(
        PlanRoot, Candidate, Inputs, CastValue(dict[str, object], PlanData["candidate"])
    )
    CheckInspection(RepoPath, PlanRoot, PlanData)
    CheckSourceBad(RepoPath, Candidate, WorkPath, Inputs)
    CheckPlanBad(RepoPath, Candidate, WorkPath, Inputs, ArchiveHash, ManifestHash)
    assert {
        RoleValue: ArtifactPin(FileValue) for RoleValue, FileValue in Inputs.items()
    } == Before
    assert ArtifactPin(Candidate / "P03-baseline-a.f3d")[0] == ArchiveHash
    assert ArtifactPin(Candidate / "P03CandidateEvidence.json")[0] == ManifestHash
