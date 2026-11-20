# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# the public smoke driver crosses real preparation worker recovery and watchdog process boundaries
def CheckOwnerLoop(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Result = Subprocess.run(
        [
            System.executable,
            "-B",
            str(RootPath / "re/automation/Pilot/SmokePilot.py"),
            "--directory",
            str(TmpPath / "Observation"),
        ],
        cwd=RootPath,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr + Result.stdout
    Evidence = JsonCodec.loads(Result.stdout)
    assert Evidence["active_recovery"] is True
    assert Evidence["idle_recovery"] is True
    assert Evidence["healthy_after_stale_deadline"] is True
    assert Evidence["fixed_window_preserved"] is True
    assert Evidence["changed_configuration_refused"] is True
