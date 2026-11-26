# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ReadJson
from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.RunWitness import (
    RunWitness,
)


# inspection must bind the prepared evidence without executing a phase or changing its files
def CheckInspection(
    RepoPath: FilePath, PlanRoot: FilePath, PlanData: dict[str, object]
) -> None:
    PlanHash, _ = ArtifactPin(PlanRoot / "plan.json")
    Arguments = ("inspect-plan", "--witness", str(PlanRoot), "--plan-sha256", PlanHash)
    FilesBefore = {
        Entry: ArtifactPin(Entry) for Entry in PlanRoot.rglob("*") if Entry.is_file()
    }
    Result = RunWitness(RepoPath, PlanRoot.parent, *Arguments)
    assert Result.returncode == 0, Result.stderr
    Receipt = ReadJson(Result.stdout)
    assert Receipt["status"] == "verified_prepared_p03_custody"
    assert Receipt["preparation_host"] == PlanData["preparation_host"]
    assert Receipt["candidate"] == PlanData["candidate"]
    assert Receipt["plan_sha256"] == PlanHash
    assert {
        Entry: ArtifactPin(Entry) for Entry in PlanRoot.rglob("*") if Entry.is_file()
    } == FilesBefore
    Archive = PlanRoot / "inputs" / "P03-baseline-a.f3d"
    Original = Archive.read_bytes()
    try:
        _ = Archive.write_bytes(Original + b"\n")
        Refused = RunWitness(RepoPath, PlanRoot.parent, *Arguments)
        assert Refused.returncode != 0 and "Pinned bytes changed" in Refused.stderr
    finally:
        _ = Archive.write_bytes(Original)
    assert ArtifactPin(Archive) == FilesBefore[Archive]
