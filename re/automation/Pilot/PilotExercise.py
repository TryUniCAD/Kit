# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath
from typing import TextIO


# real pilot commands exercise the durable controller and actual windows process container
class PilotProcess:
    # each case owns its unused store and every process started against it
    def __init__(Owner, RootPath: FilePath, Directory: FilePath) -> None:
        Owner.RootPath = RootPath
        Owner.Directory = Directory
        Owner.LogOutput: TextIO | None = None
        Owner.Owner: Subprocess.Popen[str] | None = None

    # subprocess preparation binds the archived discovery schedule before any observation begins
    def PreparePilot(Owner) -> None:
        Revision = Subprocess.check_output(
            ["git", "--no-replace-objects", "rev-parse", "HEAD"],
            cwd=Owner.RootPath,
            text=True,
        ).strip()
        Result = Subprocess.run(
            [
                System.executable,
                "-B",
                str(Owner.RootPath / "re/automation/Pilot/PreparePilot.py"),
                "--directory",
                str(Owner.Directory),
                "--source-revision",
                Revision,
            ],
            cwd=Owner.RootPath,
            capture_output=True,
            text=True,
            timeout=360,
            check=False,
        )
        assert Result.returncode == 0, Result.stderr
        assert JsonCodec.loads(Result.stdout)["planned_jobs"] == 26

    # the owner uses its public entry point while test output stays outside source control
    def StartOwner(Owner) -> None:
        Owner.LogOutput = (Owner.Directory / "TestOwner.log").open(
            "a", encoding="utf-8"
        )
        Owner.Owner = Subprocess.Popen(
            [
                System.executable,
                "-B",
                str(Owner.RootPath / "re/automation/Pilot/RunPilot.py"),
                "--directory",
                str(Owner.Directory),
            ],
            cwd=Owner.RootPath,
            stdout=Owner.LogOutput,
            stderr=Owner.LogOutput,
            text=True,
        )

    # bounded polling observes only the journal emitted by the owned watchdog process
    def AwaitEvents(
        Owner, EventName: str, Minimum: int = 1, Timeout: float = 120
    ) -> list[dict[str, object]]:
        Deadline = TimeClock.monotonic() + Timeout
        while TimeClock.monotonic() < Deadline:
            Events = Owner.ReadEvents()
            Matches = [Entry for Entry in Events if Entry.get("event") == EventName]
            if len(Matches) >= Minimum:
                return Matches
            assert Owner.Owner is not None
            assert Owner.Owner.poll() is None, (
                Owner.Directory / "TestOwner.log"
            ).read_text(encoding="utf-8")
            TimeClock.sleep(0.2)
        raise AssertionError(f"pilot did not emit {Minimum} {EventName} events")

    # recorded watchdog events are the evidence boundary for restart and continuity assertions
    def ReadEvents(Owner) -> list[dict[str, object]]:
        EventPath = Owner.Directory / "Events.jsonl"
        if not EventPath.exists():
            return []
        return [
            JsonCodec.loads(EntryText)
            for EntryText in EventPath.read_text(encoding="utf-8").splitlines()
        ]

    # explicit stop requests exercise graceful operator intervention without killing unrelated processes
    def StopOwner(Owner) -> None:
        _ = (Owner.Directory / "Stop.request").write_text(
            "process verification\n", encoding="utf-8"
        )
        if Owner.Owner is not None:
            assert Owner.Owner.wait(timeout=45) == 0, (
                Owner.Directory / "TestOwner.log"
            ).read_text(encoding="utf-8")
            Owner.Owner = None
        if Owner.LogOutput is not None:
            Owner.LogOutput.close()
            Owner.LogOutput = None
