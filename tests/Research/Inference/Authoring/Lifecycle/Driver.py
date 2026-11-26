# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from runpy import run_path as LoadScript
from subprocess import DEVNULL as KNullInput, Popen as StartProcess
from sys import argv as ArgValues, executable as PythonExe
from time import sleep as WaitTime


# a separate interpreter observes actual coordinator cleanup rather than replacing its process methods
def ObserveOwner(
    ModulePath: FilePath, Directory: FilePath, SourceRoot: FilePath, ModeValue: str
) -> dict[str, object]:
    OwnLife = LoadScript(str(ModulePath))["OwnFusionLife"]
    InputPaths = [
        Directory / FileName
        for FileName in ("Supervisor.json", "Installation.json", "Lifecycle.json")
    ]
    with OwnLife(Directory, SourceRoot, *InputPaths) as OwnerValue:
        WaitTime(1 if ModeValue == "late" else 0.15)
        OwnerValue.CheckAlive()
        OwnerPid = OwnerValue.Process.pid
    assert OwnerValue.Process.poll() is not None
    if ModeValue == "resume":
        with OwnLife(Directory, SourceRoot, *InputPaths, Resume=True) as Resumed:
            Resumed.CheckAlive()
        assert Resumed.Process.poll() is not None
    return {"owner_stopped": True, "owner_pid": OwnerPid}


# coordinator lifetime checks must prove that unrelated process ownership survives both success and failure
def RunDriver() -> None:
    ModulePath = (
        FilePath(ArgValues[1])
        / "re/automation/InferenceGrid/Authoring/FusionLifecycle.py"
    )
    PeerValue = StartProcess(
        [PythonExe, "-B", "-c", "import time; time.sleep(120)"],
        stdin=KNullInput,
        stdout=KNullInput,
        stderr=KNullInput,
    )
    try:
        try:
            ReportValue = ObserveOwner(
                ModulePath, FilePath(ArgValues[2]), FilePath(ArgValues[3]), ArgValues[4]
            )
        except RuntimeError as ErrorValue:
            ReportValue = {"failure": str(ErrorValue)}
        assert PeerValue.poll() is None
        print(EncodeJson({**ReportValue, "peer_preserved": True}))
    finally:
        PeerValue.terminate()
        _ = PeerValue.wait(timeout=15)


if __name__ == "__main__":
    RunDriver()
