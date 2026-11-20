# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterator
from pathlib import Path as FilePath
from shutil import copyfile as CopyFile
from subprocess import run as RunProcess

from pytest import fixture as Fixture

from tests.Research.Archives.FusionAdmission.CleanCheckout import CleanCheckout


# private source commits let the real command enforce clean committed verifier identities
@Fixture()
def ReplayRepo(TmpPath: FilePath) -> Iterator[FilePath]:
    SourceRoot = FilePath(__file__).resolve().parents[4]
    TargetRoot = TmpPath / "Checkout"
    _ = RunProcess(
        [
            "git",
            "clone",
            "--shared",
            "--no-checkout",
            "--quiet",
            str(SourceRoot),
            str(TargetRoot),
        ],
        check=True,
        capture_output=True,
        timeout=90,
    )
    _ = RunProcess(
        ["git", "-C", str(TargetRoot), "read-tree", "HEAD"], check=True, timeout=30
    )
    _ = RunProcess(
        ["git", "-C", str(TargetRoot), "checkout", "--", "src", "re/automation"],
        check=True,
        capture_output=True,
        timeout=30,
    )
    SourcePaths = ["re/automation/PairedEvidenceManifest.py"] + [
        f"re/automation/CaptureTools/PairedCaptures/{FileName}"
        for FileName in (
            "FusionRunEvidence.py",
            "FusionRunReadbacks.py",
            "FusionSupplement.py",
        )
    ]
    for SourcePath in SourcePaths:
        (TargetRoot / SourcePath).parent.mkdir(parents=True, exist_ok=True)
        _ = CopyFile(SourceRoot / SourcePath, TargetRoot / SourcePath)
    _ = RunProcess(
        ["git", "-C", str(TargetRoot), "add", "--", *SourcePaths],
        check=True,
        timeout=30,
    )
    _ = RunProcess(
        [
            "git",
            "-C",
            str(TargetRoot),
            "-c",
            "user.name=Evidence Fixture",
            "-c",
            "user.email=evidence@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--allow-empty",
            "-m",
            "Test - Pin supplemental verifier source",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    try:
        yield TargetRoot
    finally:
        CleanCheckout(TargetRoot, TmpPath)
