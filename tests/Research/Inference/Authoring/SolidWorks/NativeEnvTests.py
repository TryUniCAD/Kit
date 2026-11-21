# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps, loads
from os import environ
from pathlib import Path
from subprocess import run
from sys import executable, platform

from pytest import mark

from tests.Research.SupervisorClient import KRepoRoot


# native profile restoration crosses actual owned child boundaries while excluding caller secrets
@mark.skipif(platform != "win32", reason="Windows native process boundary")
def CheckNativeEnv(TmpPath: Path) -> None:
    Profile = TmpPath / "NativeProfile"
    Roaming = Profile / "Roaming"
    Scratch = TmpPath / "TaskScratch"
    Roaming.mkdir(parents=True)
    Scratch.mkdir()
    Settings = Scratch / "Host.json"
    _ = Settings.write_text(
        dumps(
            {
                "native_environment": {
                    "USERPROFILE": str(Profile),
                    "APPDATA": str(Roaming),
                }
            }
        ),
        encoding="utf-8",
    )
    Environment = dict(environ)
    Environment.update(
        {
            "KIT_PRIVATE_SECRET": "must remain private",
            "PYTHONPATH": "must_not_reach_native",
            "TEMP": str(Scratch),
        }
    )
    Process = run(
        [
            executable,
            "-B",
            str(Path(__file__).with_name("NativeChild.py")),
            str(Settings),
            str(Scratch),
        ],
        cwd=KRepoRoot,
        env=Environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    Observed = loads((Scratch / "Child.stdout").read_bytes())
    assert Observed == {
        "profile": str(Profile),
        "roaming": str(Roaming),
        "temp": str(Scratch),
        "secret_absent": True,
        "pythonpath": None,
    }
    assert (Scratch / "Child.stderr").read_bytes() == b""


# host configuration cannot replace executable lookup through native profile restoration
@mark.skipif(platform != "win32", reason="Windows native process boundary")
def CheckNativeDeny(TmpPath: Path) -> None:
    Settings = TmpPath / "Host.json"
    _ = Settings.write_text(
        dumps({"native_environment": {"PATH": str(TmpPath)}}), encoding="utf-8"
    )
    Process = run(
        [
            executable,
            "-B",
            str(Path(__file__).with_name("NativeChild.py")),
            str(Settings),
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode != 0
    assert "only reviewed Windows profile paths" in Process.stderr
    assert not (TmpPath / "Child.stdout").exists()
