# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
import signal
import time
from pathlib import Path

from Processes import (
    KILL_SIGNAL,
    process_start,
    signal_group,
    start_process,
    stop_orphan,
)
from Sessions import write_private
from Pilot.PilotFiles import AppendEvent


# the watchdog contains its supervisor descendants so an owner crash cannot leave unowned execution
class OwnerProcess:
    def __init__(self, Directory, Manifest, Remaining, Attempt):
        self.Directory = Directory
        self.Output = (Directory / f"Supervisor-{Attempt}.jsonl").open(
            "ab", buffering=0
        )
        self.Errors = (Directory / f"Supervisor-{Attempt}.stderr").open(
            "ab", buffering=0
        )
        self.Process = None
        Release = None
        try:
            Argv = [
                Manifest["python"],
                "-u",
                "-B",
                str(Path(Manifest["source"]) / "re/automation/Supervisor.py"),
                "--config",
                Manifest["config"],
                "run",
                "--max-seconds",
                str(Remaining),
            ]
            Environment = {
                Key: Value
                for Key, Value in os.environ.items()
                if not Key.startswith(
                    ("GIT_", "PYTHON", "OPENAI_", "ANTHROPIC_", "CLAUDE_", "CODEX_")
                )
            }
            Environment["GIT_NO_LAZY_FETCH"] = "1"
            self.Process, Release = start_process(
                Argv,
                Manifest["source"],
                Environment,
                self.Output.fileno(),
                self.Errors.fileno(),
            )
            self.Start = (
                self.Process.identity
                if os.name == "nt"
                else process_start(self.Process.pid)
            )
            if self.Start is None:
                raise OSError("supervisor identity unavailable before release")
            write_private(
                Directory / "OwnerProcess.json",
                {
                    "pid": self.Process.pid,
                    "start": self.Start,
                    "job_object": getattr(self.Process, "job_name", None),
                },
            )
            AppendEvent(
                Directory,
                "supervisor_started",
                supervisor_pid=self.Process.pid,
                supervisor_start=self.Start,
                attempt=Attempt,
            )
            if Release is not None:
                if os.write(Release, b"x") != 1:
                    raise OSError("supervisor gate release failed")
            else:
                self.Process.resume()
        except BaseException:
            self.CloseOwner()
            raise
        finally:
            if Release is not None:
                os.close(Release)

    # stopping targets only the process container created by this watchdog instance
    def CloseOwner(self):
        try:
            if self.Process is not None:
                if self.Process.poll() is None:
                    signal_group(self.Process.pid, signal.SIGTERM)
                    Until = time.monotonic() + 15
                    while self.Process.poll() is None and time.monotonic() < Until:
                        time.sleep(0.1)
                    if self.Process.poll() is None:
                        signal_group(self.Process.pid, KILL_SIGNAL)
                self.Process.wait(timeout=10)
                if os.name == "nt":
                    self.Process.close()
        finally:
            self.Output.close()
            self.Errors.close()


# a resumed watchdog can recover only its recorded process identity and container
def RecoverOwner(Directory):
    OwnerPath = Directory / "OwnerProcess.json"
    if not OwnerPath.exists():
        return
    Owner = json.loads(OwnerPath.read_bytes())
    if process_start(Owner["pid"]) != Owner["start"]:
        return
    if not stop_orphan(Owner["pid"], Owner["start"], 10, Owner["job_object"]):
        raise OSError("recorded supervisor owner could not be recovered")
    AppendEvent(
        Directory,
        "owner_recovered",
        supervisor_pid=Owner["pid"],
        supervisor_start=Owner["start"],
    )
