# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.SolidworksCatalog.BuildSaved import BuildSaved


# refusing existing destinations protects retained evidence from accidental regeneration overwrites
def CheckKeepOutput(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Existing"
    OutputPath.mkdir()
    SentinelPath = OutputPath / "Sentinel.txt"
    SentinelPath.write_bytes(b"user owned evidence")
    Result = BuildSaved(OutputPath)
    assert Result.returncode != 0
    assert "Output directory already exists" in Result.stderr
    assert list(OutputPath.iterdir()) == [SentinelPath]
    assert SentinelPath.read_bytes() == b"user owned evidence"
