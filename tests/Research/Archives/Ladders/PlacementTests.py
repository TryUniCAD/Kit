# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# fresh production reads must recover measured placement without rewriting historical failure evidence
def CheckPlacement(TmpPath: FilePath) -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    ReportPath = TmpPath / "Placement.json"
    Result = RunProcess(
        [
            PythonExe,
            "re/solidworks/FeatureLadderRecovery/CheckPlacement.py",
            "--output",
            str(ReportPath),
        ],
        cwd=RepoPath,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    Report = LoadJson(ReportPath.read_text())
    assert Report["native_files"] == 144
    assert Report["reader_comparisons"] == 288
    assert Report["centroid_mismatches"] == 0
    assert Report["timestamp_variants"] == 24
    assert Report["invalid_reference_rejections"] == 10
    assert Report["unqualified_reference_fallbacks"] == 9
    assert Report["rotated_frame_reads"] == 2
    assert Report["custom_plane_reads"] == 2
    assert Report["multi_sketch_owner_scans"] == 1
    assert Report["fresh_native_acceptance"] is False
    assert Report["native_conversion_acceptance"] is False
