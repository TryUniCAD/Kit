# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe, platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.Windows.Readback.InstallReadback import InstallReadback
from tests.Research.Windows.Readback.ReadbackGit import ReadbackGit


# listener admission must reject changed safety helpers before creating a queue or launching cad
@TestMark.skipif(HostPlatform != "win32", reason="Windows listener admission")
@TestMark.parametrize(
    "HelperName", ("WindowsIdentity.py", "WindowsRecords.py", "SolidWorksProgress.py")
)
@TestMark.parametrize("HasReplacement", (False, True))
def CheckSourcePins(TmpPath: FilePath, HelperName: str, HasReplacement: bool) -> None:
    RootPath, ConfigPath = InstallReadback(TmpPath)
    RelativePath = "re/automation/ApplicationWorkers/" + HelperName
    HelperPath = RootPath / RelativePath
    BeforeBlob = ReadbackGit(RootPath, "rev-parse", "HEAD:" + RelativePath)
    _ = HelperPath.write_bytes(HelperPath.read_bytes() + b"\n# fixture drift\n")
    if HasReplacement:
        AfterBlob = ReadbackGit(RootPath, "hash-object", "-w", str(HelperPath))
        _ = ReadbackGit(RootPath, "replace", BeforeBlob, AfterBlob)
        assert ReadbackGit(RootPath, "show", "HEAD:" + RelativePath).endswith(
            "fixture drift"
        )
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(
                RootPath
                / "re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py"
            ),
            "--installation",
            str(ConfigPath),
            "listen",
            "--interop",
            str(ConfigPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=25,
    )
    assert Result.returncode != 0
    assert (
        "application input differs from the installed trusted revision" in Result.stderr
    )
    assert not (TmpPath / "Endpoint").exists()
