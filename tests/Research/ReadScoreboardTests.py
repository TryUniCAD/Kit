# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
import subprocess
import sys
import unicodedata

from tests.Research.SupervisorClient import KRepoRoot

# a strict Fusion decode with no unresolved items exercises the fully read state
StrictFusion = "re/Fusion/Study/extents-f0f33a9a605f/taper.f3d"

# a partial Fusion decode exercises strict refusal and feature attribution
PartialFusion = "re/Fusion/Study/edgemodes-52695761f185/chamfer_multiple.f3d"

# a pinned real-world part carries an accented name to exercise path normalisation
SolidWorksPart = "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/ARBOL DE LEVAS DE ADMISIÓN_DERECHO.SLDPRT"


# the scoreboard is exercised through its own command and real pinned blobs
def RunScoreboard(Output: Path, *Assets: str, Expected: int = 0):
    Command = [
        sys.executable,
        "-B",
        str(KRepoRoot / "re/automation/ReadScoreboard.py"),
        "--output",
        str(Output),
    ]
    for Asset in Assets:
        Command += ["--asset", Asset]
    Result = subprocess.run(
        Command, cwd=KRepoRoot, capture_output=True, text=True, check=False, timeout=300
    )
    assert Result.returncode == Expected, Result.stderr
    return Result


# totals, read modes, feature attribution and the Markdown page agree for a mixed subset
def CheckMixedSubset(TmpPath: Path):
    Output = TmpPath / "Board"
    RunScoreboard(
        Output,
        StrictFusion,
        PartialFusion,
        unicodedata.normalize("NFD", SolidWorksPart),
    )
    Report = json.loads((Output / "Scoreboard.json").read_bytes())
    assert Report["byte_accounting"] == "unavailable"
    Fusion = Report["summary"]["fusion"]
    assert (Fusion["files"], Fusion["strict"], Fusion["partial"]) == (2, 1, 1)
    assert Fusion["fully_read"] == 1
    Rows = {Row["path"]: Row for Row in Report["files"]}
    assert (
        Rows[StrictFusion]["fully_read"] is True
        and Rows[StrictFusion]["unresolved"] == 0
    )
    Partial = Rows[PartialFusion]
    assert Partial["reader_mode"] == "partial" and Partial["strict_rejection"]
    assert any(Area.startswith("feature: ") for Area in Partial["unresolved_areas"])
    assert sum(Partial["unresolved_areas"].values()) == Partial["unresolved"]
    SolidWorks = Report["summary"]["solidworks"]
    assert SolidWorks["files"] == 1 and SolidWorks["rejected"] == 0
    Page = (Output / "Scoreboard.md").read_text(encoding="utf-8")
    assert (
        "| fusion | 2 | 1 | 1 |" in Page
        and "## solidworks: areas blocking a full read" in Page
    )


# reused output directories and unpinned paths are refused before any decoding
def CheckRefusals(TmpPath: Path):
    Output = TmpPath / "Board"
    Output.mkdir()
    assert (
        "output already exists"
        in RunScoreboard(Output, StrictFusion, Expected=1).stderr
    )
    Fresh = TmpPath / "Fresh"
    assert (
        "pinned native corpus path"
        in RunScoreboard(Fresh, "re/absent.f3d", Expected=1).stderr
    )
    assert not Fresh.exists()
