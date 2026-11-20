# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe, platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.Readback.InstallReadback import InstallReadback
from tests.Research.Windows.Readback.ReadbackGit import ReadbackGit

# the real companion source gate must execute before installation discovery or any native launch
KValidateScript = """import sys
sys.path.insert(0, sys.argv[1])
from RunSolidWorksBossWitness import SourcePins
SourcePins(sys.argv[2])
print('validated Boss collector source pins')
"""


# real python and git processes expose source replacements that mocks would miss
@TestMark.skipif(HostPlatform != "win32", reason="Windows Boss source admission")
@TestMark.parametrize(
    "TestTarget,HasReplacement",
    (
        ("clean", False),
        ("collector", False),
        ("collector", True),
        ("launcher", False),
        ("launcher", True),
    ),
)
def CheckBossSource(TmpPath: FilePath, TestTarget: str, HasReplacement: bool) -> None:
    RootPath, _ = InstallReadback(TmpPath)
    for SourcePath in (KRepoRoot / "re/automation").rglob("*"):
        if SourcePath.is_file() and SourcePath.suffix in (".py", ".cs", ".ps1"):
            Destination = RootPath / SourcePath.relative_to(KRepoRoot)
            Destination.parent.mkdir(parents=True, exist_ok=True)
            _ = Destination.write_bytes(SourcePath.read_bytes())
    _ = ReadbackGit(RootPath, "add", "re")
    _ = ReadbackGit(
        RootPath,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-m",
        "test: pin Boss source fixture",
    )
    Revision = ReadbackGit(RootPath, "rev-parse", "HEAD")
    if TestTarget != "clean":
        FileName = (
            "BossWitnessReadback.cs"
            if TestTarget == "collector"
            else "RunBossWitness.ps1"
        )
        RelativePath = "re/automation/PairedCaptures/SolidWorksAuthoring/" + FileName
        FileValue = RootPath / RelativePath
        BeforeBlob = ReadbackGit(RootPath, "rev-parse", "HEAD:" + RelativePath)
        Comment = (
            b"\n// fixture source drift\n"
            if FileName.endswith(".cs")
            else b"\n# fixture source drift\n"
        )
        _ = FileValue.write_bytes(FileValue.read_bytes() + Comment)
        if HasReplacement:
            AfterBlob = ReadbackGit(RootPath, "hash-object", "-w", str(FileValue))
            _ = ReadbackGit(RootPath, "replace", BeforeBlob, AfterBlob)
            assert ReadbackGit(RootPath, "show", "HEAD:" + RelativePath).endswith(
                "fixture source drift"
            )
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            "-c",
            KValidateScript,
            str(RootPath / "re/automation"),
            Revision,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=25,
    )
    if TestTarget == "clean":
        assert Result.returncode == 0, Result.stderr
        assert "validated Boss collector source pins" in Result.stdout
    else:
        assert Result.returncode != 0
        assert "collector source changed" in Result.stderr
