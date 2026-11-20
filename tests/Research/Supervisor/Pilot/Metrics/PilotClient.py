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

# process coverage needs this checkout rather than the source directory of another worktree
KRepoRoot = FilePath(__file__).resolve().parents[5]


# reporting checks cross the actual command boundary while proving the ledger remains unchanged
def RunReport(
    RootPath: FilePath, *Arguments: str, ExitCode: int = 0
) -> dict[str, object]:
    Database = RootPath / "State" / "ledger.sqlite3"
    Before = Database.read_bytes()
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/PilotMetrics/ReportPilot.py"),
            *Arguments,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert Process.returncode == ExitCode, Process.stderr
    assert Database.read_bytes() == Before
    Result: dict[str, object] = JsonCodec.loads(Process.stdout) if ExitCode == 0 else {}
    return Result


# fixture writes retain exactly the bytes used in their evidence pins
def WriteRecord(FileName: FilePath, Value: dict[str, object]) -> str:
    from hashlib import sha256 as ShaDigest

    Content = JsonCodec.dumps(Value, sort_keys=True).encode("utf-8")
    _ = FileName.write_bytes(Content)
    return ShaDigest(Content).hexdigest()
