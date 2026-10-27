# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import pathlib as Pathlib
import tempfile as Tempfile
from unittest import TestCase as UnitTestCase

from tests.Policy.RepoFixture import RepoFixture
from tests.Policy.SpdxHeadersTest import LoadGuard


# revision focused fixtures bind materialized files to one exact commit identity
class TestHeadGuard(UnitTestCase):

    # exact commit and worktree checks prevent symbolic revisions or a stale materialized head
    def TestExactHead(self) -> None:
        GuardModule = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Source.py")
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.MoveFile("Source.py", "Target.py")
            HeadRef = FixtureInfo.CommitAll("head")
            self.assertTrue(GuardModule.IsCommit(HeadRef, RootPath))
            self.assertFalse(GuardModule.IsCommit("HEAD", RootPath))
            self.assertEqual(
                GuardModule.GetDiffFiles(BaseRef, HeadRef, RootPath), ["Target.py"]
            )
            WorktreeRoot, ReasonText = GuardModule.CheckWorktree(RootPath, HeadRef)
            self.assertEqual(WorktreeRoot, RootPath.resolve(), ReasonText)
            WorktreeRoot, ReasonText = GuardModule.CheckWorktree(RootPath, "0" * 40)
            self.assertIsNone(WorktreeRoot, ReasonText)
