# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

# disposable coordinators retain the fixed production entry point without launching a native application
KCoordinatorCode = """
import argparse
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser(allow_abbrev=False)
for name in ('config', 'installation', 'lifecycle', 'queue-directory'):
    parser.add_argument('--' + name, required=True)
args = parser.parse_args()
directory = Path(args.queue_directory)
(directory / 'CoordinatorArgs.json').write_text(json.dumps(vars(args)), encoding='utf-8')
print('disposable coordinator fixture started', flush=True)
mode = (directory / 'Mode.txt').read_text(encoding='utf-8')
if mode == 'early':
    raise SystemExit(7)
if mode == 'late':
    time.sleep(.7)
    raise SystemExit(9)
while True:
    time.sleep(.05)
"""


# each process scenario uses new files so retained logs cannot hide an earlier coordinator failure
def RunLifeChild(TmpPath: FilePath, ModeValue: str) -> ChildResult[str]:
    RepoRoot = FilePath(__file__).resolve().parents[5]
    FixtureRoot = TmpPath / "FixtureSource"
    WorkerPath = (
        FixtureRoot / "re/automation/ApplicationWorkers/FusionLifecycleOwner.py"
    )
    WorkerPath.parent.mkdir(parents=True)
    _ = WorkerPath.write_text(KCoordinatorCode, encoding="utf-8")
    RunDirectory = TmpPath / "Run"
    RunDirectory.mkdir()
    _ = (RunDirectory / "Mode.txt").write_text(ModeValue, encoding="utf-8")
    for FileName in ("Supervisor.json", "Installation.json", "Lifecycle.json"):
        _ = (RunDirectory / FileName).write_text("{}", encoding="utf-8")
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(FilePath(__file__).with_name("Driver.py")),
            str(RepoRoot),
            str(RunDirectory),
            str(FixtureRoot),
            ModeValue,
        ],
        cwd=RepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


# stopping a catalogue must stop its coordinator while unrelated application ownership remains intact
def CheckLifecycle(TmpPath: FilePath) -> None:
    ResultValue = RunLifeChild(TmpPath, "normal")
    assert ResultValue.returncode == 0, ResultValue.stderr
    ReportValue = DecodeJson(ResultValue.stdout)
    assert ReportValue["owner_stopped"] and ReportValue["peer_preserved"]
    Arguments = DecodeJson((TmpPath / "Run/CoordinatorArgs.json").read_bytes())
    assert Arguments["queue_directory"] == str((TmpPath / "Run").resolve())
    assert Arguments["config"] == str((TmpPath / "Run/Supervisor.json").resolve())
    assert Arguments["installation"] == str(
        (TmpPath / "Run/Installation.json").resolve()
    )
    assert Arguments["lifecycle"] == str((TmpPath / "Run/Lifecycle.json").resolve())


# resumed supervision preserves all earlier coordinator diagnostics in its original run directory
def CheckLifeResume(TmpPath: FilePath) -> None:
    ResultValue = RunLifeChild(TmpPath, "resume")
    assert ResultValue.returncode == 0, ResultValue.stderr
    assert DecodeJson(ResultValue.stdout)["peer_preserved"]
    LogValue = (TmpPath / "Run/FusionLifecycle.log").read_text(encoding="utf-8")
    assert LogValue.count("disposable coordinator fixture started") == 2


# a coordinator that exits during startup cannot silently leave the native phase queue unattended
def CheckEarlyExit(TmpPath: FilePath) -> None:
    ResultValue = RunLifeChild(TmpPath, "early")
    assert ResultValue.returncode == 0, ResultValue.stderr
    ReportValue = DecodeJson(ResultValue.stdout)
    assert "code 7" in ReportValue["failure"] and ReportValue["peer_preserved"]


# later coordinator failures remain observable while dependent catalogue workers are active
def CheckLateExit(TmpPath: FilePath) -> None:
    ResultValue = RunLifeChild(TmpPath, "late")
    assert ResultValue.returncode == 0, ResultValue.stderr
    ReportValue = DecodeJson(ResultValue.stdout)
    assert "code 9" in ReportValue["failure"] and ReportValue["peer_preserved"]
