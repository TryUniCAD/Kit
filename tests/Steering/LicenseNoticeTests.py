import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMarks

from tests.Policy.RepoFixture import RepoFixture
from tests.Steering.RationaleCommentsTests import RunModule

# independently authored legal text exercises the public policies without trusting their recognizer constant
KNoticeText = """\
# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.
"""

# compliant owned code isolates legal notice behavior from unrelated declaration findings
KCleanSource = """\

# known values remain explicit because this fixture checks declaration policy
KSourceValue = 1
"""

# malformed notice variants must remain visible because legal recognition cannot admit ordinary commentary
KSourceCases = (
    (KNoticeText + KCleanSource, ""),
    ((KNoticeText + KCleanSource).replace("\n", "\r\n"), ""),
    (
        KNoticeText + "\n# ordinary explanations remain forbidden\n" + KCleanSource,
        "CMT002",
    ),
    (KCleanSource + "\n" + KNoticeText, "CMT002"),
    (KNoticeText.replace("material breach", "minor breach") + KCleanSource, "CMT002"),
    (KNoticeText.rsplit("\n", 2)[0] + "\n" + KCleanSource, "CMT002"),
    (KNoticeText + "\n" + KNoticeText + KCleanSource, "CMT002"),
    (
        "# ordinary leading explanation stays forbidden\n" + KNoticeText + KCleanSource,
        "CMT002",
    ),
    (KCleanSource.rstrip() + "  " + KNoticeText, "CMT002"),
    (KNoticeText + "\nKSourceValue = 1\n", "RAT001"),
    (KNoticeText.replace("\n", "\v") + KCleanSource, "CMT002"),
)


# both real checker entry forms must preserve exact notice and rationale decisions outside the repository directory
@TestMarks.parametrize("SourceText,RuleCode", KSourceCases)
@TestMarks.parametrize("EntryMode", ("module", "script"))
def CheckNoticeCli(
    TmpPath: FilePath, SourceText: str, RuleCode: str, EntryMode: str
) -> None:
    TargetPath = TmpPath / "Alpha.py"
    _ = TargetPath.write_bytes(SourceText.encode("utf-8"))
    SourceRoot = FilePath(__file__).resolve().parents[2]
    ArgItems = [System.executable]
    if EntryMode == "module":
        ArgItems.extend(["-m", "tools.Steering.SteeringCompliance"])
    else:
        ArgItems.append(str(SourceRoot / "tools/Steering/SteeringCompliance.py"))
    ResultInfo = Subprocess.run(
        [*ArgItems, str(TargetPath)],
        cwd=SourceRoot if EntryMode == "module" else TmpPath,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ResultInfo.returncode == bool(RuleCode), (
        ResultInfo.stdout + ResultInfo.stderr
    )
    if RuleCode:
        assert RuleCode.replace("CMT002", "CMT001") in ResultInfo.stdout


# actual git revisions must enforce new comment and missing rationale rules while admitting only the complete notice
@TestMarks.parametrize("SourceText,RuleCode", KSourceCases)
def CheckNoticeDiff(TmpPath: FilePath, SourceText: str, RuleCode: str) -> None:
    FixtureInfo = RepoFixture(TmpPath)
    FixtureInfo.WriteFile("Alpha.py", KCleanSource)
    BaseRef = FixtureInfo.CommitAll("owned source")
    _ = (TmpPath / "Alpha.py").write_bytes(SourceText.encode("utf-8"))
    HeadRef = FixtureInfo.CommitAll("notice boundary")
    ResultInfo = RunModule(TmpPath, BaseRef, HeadRef)
    assert ResultInfo.returncode == bool(RuleCode), (
        ResultInfo.stdout + ResultInfo.stderr
    )
    if RuleCode:
        assert RuleCode in ResultInfo.stdout
