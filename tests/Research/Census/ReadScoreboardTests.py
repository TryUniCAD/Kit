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

# a strict fusion decode with no unresolved items exercises the fully read state
KStrictFusion = "re/Fusion/Study/extents-f0f33a9a605f/taper.f3d"

# a partial fusion decode exercises strict refusal and feature attribution
KPartialFusion = "re/Fusion/Study/edgemodes-52695761f185/chamfer_multiple.f3d"

# a pinned solidworks part with an accented name exercises path normalisation
KSolidWorksPart = (
    "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/"
    "ARBOL DE LEVAS DE ADMISIÓN_DERECHO.SLDPRT"
)


# the scoreboard is exercised through its own command and real pinned blobs
def RunScoreboard(
    Output: Path, *Assets: str, Expected: int = 0
) -> subprocess.CompletedProcess[str]:
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


# totals read modes feature attribution and the markdown page agree for a mixed subset
def CheckMixedSet(TmpPath: Path) -> None:
    Output = TmpPath / "Board"
    _ = RunScoreboard(
        Output,
        KStrictFusion,
        KPartialFusion,
        unicodedata.normalize("NFD", KSolidWorksPart),
    )
    Report = json.loads((Output / "Scoreboard.json").read_bytes())
    assert Report["byte_accounting"] == "unavailable"
    Fusion = Report["summary"]["fusion"]
    assert (Fusion["files"], Fusion["strict"], Fusion["partial"]) == (2, 1, 1)
    assert Fusion["fully_read"] == 1
    Records = {Record["path"]: Record for Record in Report["files"]}
    assert Records[KStrictFusion]["fully_read"] is True
    assert Records[KStrictFusion]["unresolved"] == 0
    Partial = Records[KPartialFusion]
    assert Partial["reader_mode"] == "partial" and Partial["strict_rejection"]
    assert any(Region.startswith("feature: ") for Region in Partial["unresolved_areas"])
    assert sum(Partial["unresolved_areas"].values()) == Partial["unresolved"]
    SolidWorks = Report["summary"]["solidworks"]
    assert (
        SolidWorks["files"] == 1 and SolidWorks["strict"] + SolidWorks["partial"] == 1
    )
    Normal = {
        unicodedata.normalize("NFC", Location): Value
        for Location, Value in Records.items()
    }
    PartRecord = Normal[unicodedata.normalize("NFC", KSolidWorksPart)]
    assert PartRecord["outcome"] == "decoded" and PartRecord["features"]
    Markdown = (Output / "Scoreboard.md").read_text(encoding="utf-8")
    assert "| fusion | 2 | 1 | 1 |" in Markdown
    assert "## solidworks: areas blocking a full read" in Markdown


# reused output directories and unpinned paths are refused before any decoding
def CheckRefusals(TmpPath: Path) -> None:
    Output = TmpPath / "Board"
    Output.mkdir()
    Refused = RunScoreboard(Output, KStrictFusion, Expected=1)
    assert "output already exists" in Refused.stderr
    Fresh = TmpPath / "Fresh"
    Unpinned = RunScoreboard(Fresh, "re/absent.f3d", Expected=1)
    assert "pinned native corpus path" in Unpinned.stderr
    assert not Fresh.exists()
