# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.Readback.ReadbackGit import ReadbackGit


# a private snapshot permits source tampering without changing any user checkout
def InstallReadback(TmpPath: FilePath) -> tuple[FilePath, FilePath]:
    RootPath = TmpPath / "Installed"
    RootPath.mkdir()
    ReadbackGit(RootPath, "init", "--initial-branch=fixture/readback")
    ReadbackGit(RootPath, "config", "core.autocrlf", "false")
    for RelativePath in (
        "ApplicationWorkers/SolidWorksReadbackWorker.py",
        "ApplicationWorkers/SolidWorksProgress.py",
        "ApplicationWorkers/SolidWorksAvailability.py",
        "ApplicationWorkers/ApplicationProtocol.py",
        "ApplicationWorkers/WindowsIdentity.py",
        "ApplicationWorkers/WindowsRecords.py",
        "PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1",
        "PairedCaptures/SolidWorksAuthoring/ReadbackProgress.cs",
    ):
        Destination = RootPath / "re/automation" / RelativePath
        Destination.parent.mkdir(parents=True, exist_ok=True)
        _ = Destination.write_bytes(
            (KRepoRoot / "re/automation" / RelativePath).read_bytes()
        )
    ReadbackGit(RootPath, "add", "re")
    ReadbackGit(
        RootPath,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-m",
        "test: pin readback fixture",
    )
    ConfigPath = TmpPath / "Installation.json"
    _ = ConfigPath.write_text(
        EncodeJson(
            {
                "version": 1,
                "installation": "fixture:readback",
                "application": "solidworks",
                "endpoint": str(TmpPath / "Endpoint"),
                "source_root": str(RootPath),
                "source_revision": ReadbackGit(RootPath, "rev-parse", "HEAD"),
            }
        ),
        encoding="utf-8",
    )
    return RootPath, ConfigPath
