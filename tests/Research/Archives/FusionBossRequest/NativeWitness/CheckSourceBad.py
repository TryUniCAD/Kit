# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.NativeWitness.ArtifactPin import (
    ArtifactPin,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.ChangeManifest import (
    ChangeManifest,
)
from tests.Research.Archives.FusionBossRequest.NativeWitness.RunPrepare import (
    RunPrepare,
)


# custody must refuse source bytes and semantic claims even with a recomputed manifest digest
def CheckSourceBad(
    RepoPath: FilePath,
    Candidate: FilePath,
    WorkPath: FilePath,
    Inputs: dict[str, FilePath],
) -> None:
    ArchivePath = Candidate / "P03-baseline-a.f3d"
    ReportPath = Candidate / "P03CandidateEvidence.json"
    ArchiveBytes, ReportBytes = ArchivePath.read_bytes(), ReportPath.read_bytes()
    ArchiveHash, ReportHash = ArtifactPin(ArchivePath)[0], ArtifactPin(ReportPath)[0]
    for Change, Diagnostic in (
        ("archive", "P03 replay input digest differs"),
        ("manifest", "P03 replay manifest digest differs"),
        (
            "roles",
            "P03 replay report differs from independently reproduced strict and typed evidence",
        ),
        ("generators", "P03 replay program report custody differs"),
    ):
        Variant = WorkPath / f"Candidate-{Change}"
        Variant.mkdir()
        _ = (Variant / ArchivePath.name).write_bytes(
            ArchiveBytes + (b"\n" if Change == "archive" else b"")
        )
        Changed = (
            ChangeManifest(ReportBytes, Change)
            if Change in ("roles", "generators")
            else ReportBytes
        )
        Altered = Variant / ReportPath.name
        _ = Altered.write_bytes(Changed + (b"\n" if Change == "manifest" else b""))
        OutputPath = WorkPath / f"Refused-{Change}"
        Digest = (
            ArtifactPin(Altered)[0] if Change in ("roles", "generators") else ReportHash
        )
        Result = RunPrepare(RepoPath, Variant, OutputPath, Inputs, ArchiveHash, Digest)
        assert Result.returncode != 0 and Diagnostic in Result.stderr, Result.stderr
        assert not OutputPath.exists()
    assert (
        ArchivePath.read_bytes() == ArchiveBytes
        and ReportPath.read_bytes() == ReportBytes
    )
