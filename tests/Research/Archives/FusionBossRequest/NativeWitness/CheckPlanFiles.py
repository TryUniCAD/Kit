# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)


# prepared operator inputs must preserve each independent byte sequence under its fixed name
def CheckPlanFiles(
    PlanRoot: FilePath,
    Candidate: FilePath,
    Inputs: dict[str, FilePath],
    Report: dict[str, object],
) -> None:
    ReplayFiles = {
        "request": "P03Request.json",
        "witness": "P03SourceWitness.json",
        "seed_helper": "SeedHelper.py",
        "snapshot_builder": "ProbePrismSnapshot.py",
        "snapshot_owners": "SnapshotOwners.py",
    }
    Generation = ReadJson((Candidate / "P03CandidateEvidence.json").read_bytes())
    assert Report["public_strict_read"] == Generation["public_strict_read"]
    assert Report["target_snapshot"] == Generation["target_snapshot"]
    PinsValue = CastValue(dict[str, dict[str, object]], Report["replay_inputs"])
    assert set(PinsValue) == set(ReplayFiles) == set(Inputs)
    for RoleValue, NameValue in ReplayFiles.items():
        Expected, SizeValue = ArtifactPin(Inputs[RoleValue])
        assert PinsValue[RoleValue] == {
            "file": NameValue,
            "sha256": Expected,
            "size_bytes": SizeValue,
        }
    Originals = Inputs.copy()
    for RoleValue, NameValue in (
        ("input", "P03-baseline-a.f3d"),
        ("manifest", "P03CandidateEvidence.json"),
    ):
        Expected, SizeValue = ArtifactPin(Candidate / NameValue)
        assert Report[RoleValue] == {
            "file": NameValue,
            "sha256": Expected,
            "size_bytes": SizeValue,
        }
        ReplayFiles[RoleValue], Originals[RoleValue] = NameValue, Candidate / NameValue
    Retained = PlanRoot / "inputs"
    assert {Entry.name for Entry in Retained.iterdir()} == set(ReplayFiles.values())
    for RoleValue, NameValue in ReplayFiles.items():
        assert (Retained / NameValue).read_bytes() == Originals[RoleValue].read_bytes()
