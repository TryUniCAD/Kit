# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import unittest as UnitTest

from tools.Policy.GitFailure import GitFailure
from tools.Policy.ParseGitPaths import ParseGitPaths


# byte parser coverage prevents whitespace and malformed framing from becoming path ambiguity
class TestGitPaths(UnitTest.TestCase):

    # unusual legal whitespace must survive because line parsing would silently split filenames
    def CheckNullPaths(CaseSelf) -> None:
        PathData = b"Alpha.py\0Line\nBreak.py\0Tab\tName.py\0"
        CaseSelf.assertEqual(
            ParseGitPaths(PathData),
            ("Alpha.py", "Line\nBreak.py", "Tab\tName.py"),
        )

    # malformed records must fail closed because partial path sets could approve violations
    def CheckBadFraming(CaseSelf) -> None:
        with CaseSelf.assertRaises(GitFailure):
            ParseGitPaths(b"Alpha.py")
        with CaseSelf.assertRaises(GitFailure):
            ParseGitPaths(b"Alpha.py\0\0")
        CaseSelf.assertEqual(ParseGitPaths(b""), ())
