# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from subprocess import run
from sys import executable, platform

from pytest import mark

from tests.Research.SupervisorClient import KRepoRoot


# a real powershell refusal proves owned process startup preserves separate output handle identities
@mark.skipif(platform != "win32", reason="Windows native process boundary")
def CheckPhaseStart(TmpPath: Path) -> None:
    _ = (TmpPath / "ConfiguredCase.json").write_text("{}\n", encoding="utf-8")
    Process = run(
        [executable, "-B", str(Path(__file__).with_name("RunPhase.py")), str(TmpPath)],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Process.returncode != 0
    assert "SOLIDWORKS authoring phase failed inspect" in Process.stderr
    NativeError = (
        (TmpPath / "first.stderr.log").read_bytes().decode("utf-8", errors="replace")
    )
    assert "MissingExecutable.exe" in NativeError
    assert (TmpPath / "first.log").is_file()
    assert not (TmpPath / "first-owner.json").exists()
