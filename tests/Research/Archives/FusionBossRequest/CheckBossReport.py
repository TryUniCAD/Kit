# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.FusionBossRequest.BossArcProof import BossArcProof
from tests.Research.Archives.FusionBossRequest.CheckOperandMap import CheckOperandMap
from tests.Research.Archives.FusionBossRequest.CheckSnapshotPins import CheckSnapPins
from tests.Research.Archives.FusionBossRequest.CheckPrismState import CheckPrismState


# the sealed report must bind actual archive bytes and qualify only observed target semantics
def CheckBossReport(
    ReportPath: FilePath,
    Witness: FilePath,
    ArchiveBytes: bytes,
    Proof: BossArcProof,
    MirrorRoot: FilePath,
) -> None:
    Report = CastValue(dict[str, object], ReadJson(ReportPath.read_bytes()))
    assert (
        Report["source_witness_sha256"] == HashBytes(Witness.read_bytes()).hexdigest()
    )
    assert Report["source_witness"] == ReadJson(Witness.read_bytes())
    assert (
        Report["source_operation"] == "join" and Report["target_operation"] == "create"
    )
    assert Report["vendor_loadable"] is False
    assert Report["application_usable"] is False
    assert Report["whole_source_admission"] is False
    assert Report["public_strict_read"] == Proof.PublicRead
    assert Report["target_snapshot"] == Proof.Snapshot
    CheckSnapPins(MirrorRoot, Report["snapshot_helpers"])
    (Candidate,) = CastValue(list[dict[str, object]], Report["candidates"])
    assert Candidate["file"] == "P03-baseline-a.f3d"
    assert Candidate["archive_sha256"] == HashBytes(ArchiveBytes).hexdigest()
    assert Candidate["archive_bytes"] == len(ArchiveBytes)
    TargetBody = CastValue(dict[str, object], Candidate["target_body"])
    assert TargetBody["operation"] == "new_body" and TargetBody["volume_mm3"] == 8000
    assert Report["target_settings_observers"] == Proof.Settings
    CheckOperandMap(Report["operand_order"])
    CheckPrismState(Report["vendor_prism_projection"])
