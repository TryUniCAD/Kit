# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.CheckBossReport import CheckBossReport
from tests.Research.Archives.FusionBossRequest.CheckHelperBad import CheckHelperBad
from tests.Research.Archives.FusionBossRequest.CheckObserverBad import CheckObsReject
from tests.Research.Archives.FusionBossRequest.CheckRefusals import CheckRefusals
from tests.Research.Archives.FusionBossRequest.CopySeedHelper import CopySeedHelper
from tests.Research.Archives.FusionBossRequest.CopySnapshot import CopySnapshot
from tests.Research.Archives.FusionBossRequest.MirrorBossCode import MirrorBossCode
from tests.Research.Archives.FusionBossRequest.PrepareBoss import PrepareBoss
from tests.Research.Archives.FusionBossRequest.ReplayBoss import ReplayBoss
from tests.Research.Archives.FusionBossRequest.VerifyBossArc import VerifyBossArc


# the source derived boss must preserve its relation roles in repeatable source free archives
def TestBossReplay(TmpPath: FilePath) -> None:
    SourceRoot = FilePath(__file__).resolve().parents[4]
    PrepPath = PrepareBoss(SourceRoot, TmpPath)
    MirrorRoot = TmpPath / "Code"
    MirrorBossCode(SourceRoot, MirrorRoot)
    CopySeedHelper(SourceRoot, MirrorRoot / "SeedHelper.py")
    CopySnapshot(SourceRoot, MirrorRoot)
    Request = PrepPath / "P03Request.json"
    Witness = PrepPath / "P03SourceWitness.json"
    FirstPath = TmpPath / "First"
    LaterPath = TmpPath / "Later"
    for OutputPath in (FirstPath, LaterPath):
        Result = ReplayBoss(MirrorRoot, Request, Witness, OutputPath)
        assert Result.returncode == 0, Result.stderr
    ArchiveName = "P03-baseline-a.f3d"
    ArchiveBytes = (FirstPath / ArchiveName).read_bytes()
    assert ArchiveBytes == (LaterPath / ArchiveName).read_bytes()
    ReportPath = FirstPath / "P03CandidateEvidence.json"
    assert ReportPath.read_bytes() == (LaterPath / ReportPath.name).read_bytes()
    CheckBossReport(
        ReportPath, Witness, ArchiveBytes, VerifyBossArc(ArchiveBytes), MirrorRoot
    )
    CheckObsReject(MirrorRoot, TmpPath, ArchiveBytes)
    CheckRefusals(MirrorRoot, PrepPath, TmpPath)
    CheckHelperBad(MirrorRoot, PrepPath, TmpPath)
