# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
import time
from pathlib import Path

from Processes import process_start
from Pilot.OwnerProcess import OwnerProcess, RecoverOwner
from Pilot.PilotFiles import AppendEvent
from Pilot.SourcePins import VerifyPins


# fresh supervisor capacity publication distinguishes active supervision from watchdog uptime alone
def Heartbeat(Directory, Owner):
    Capacity = Directory / "State/supervisor-capacity.json"
    try:
        Record = json.loads(Capacity.read_bytes())
        AgeValue = max(0.0, time.time() - Capacity.stat().st_mtime)
        Identity = Record["owner"]
        Healthy = (
            process_start(Identity["pid"]) == Identity["start"]
            and HasOwnedProcess(Owner, Identity["pid"])
            and AgeValue < 60
        )
        return AgeValue, Healthy, Identity
    except (OSError, ValueError, KeyError, TypeError):
        return None, False, None


# virtual environment launchers require descendant membership rather than launcher pid equality
def HasOwnedProcess(Owner, ProcessId):
    if os.name == "nt":
        import pywintypes
        import win32api
        import win32con
        import win32job

        try:
            Handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, ProcessId
            )
        except pywintypes.error:
            return False
        try:
            return bool(win32job.IsProcessInJob(Handle, Owner.Process.job))
        finally:
            Handle.Close()
    return os.getpgid(ProcessId) == Owner.Process.pid


# bounded recovery preserves a fixed observation deadline and parks a persistent infrastructure failure
def WatchdogLoop(Directory, Manifest, Window, IsStopping):
    RecoverOwner(Directory)
    Journal = Directory / "Events.jsonl"
    Events = (
        [json.loads(Line) for Line in Journal.read_text(encoding="utf-8").splitlines()]
        if Journal.exists()
        else []
    )
    Attempts = sum(Row["event"] == "supervisor_started" for Row in Events)
    if any(Row["event"] == "circuit_open" for Row in Events):
        raise ValueError(
            "pilot circuit is open and requires a recorded operator review"
        )
    while time.time() < Window["planned_until"]:
        if IsStopping() or (Directory / "Stop.request").exists():
            AppendEvent(Directory, "operator_stop")
            return 0
        VerifyPins(Manifest)
        if Attempts >= 9:
            AppendEvent(
                Directory,
                "circuit_open",
                reason="supervisor_restart_budget_exhausted",
                launches=Attempts,
            )
            return 2
        Attempts += 1
        Owner = OwnerProcess(
            Directory, Manifest, Window["planned_until"] - time.time(), Attempts
        )
        Launched = time.monotonic()
        LastBeat = LastPins = Launched - 30
        Stale = False
        try:
            while (
                Owner.Process.poll() is None and time.time() < Window["planned_until"]
            ):
                if IsStopping() or (Directory / "Stop.request").exists():
                    AppendEvent(Directory, "operator_stop")
                    return 0
                NowMono = time.monotonic()
                if NowMono - LastBeat >= 30:
                    AgeValue, Healthy, Identity = Heartbeat(Directory, Owner)
                    AppendEvent(
                        Directory,
                        "heartbeat",
                        supervisor_pid=Owner.Process.pid,
                        supervisor_start=Owner.Start,
                        capacity_owner=Identity,
                        supervisor_heartbeat_age_seconds=AgeValue,
                        supervisor_healthy=Healthy,
                        remaining_seconds=max(0, Window["planned_until"] - time.time()),
                    )
                    LastBeat = NowMono
                    if NowMono - Launched > 60 and not Healthy:
                        Stale = True
                        AppendEvent(
                            Directory,
                            "supervisor_stale",
                            supervisor_pid=Owner.Process.pid,
                        )
                        break
                if NowMono - LastPins >= 300:
                    VerifyPins(Manifest)
                    LastPins = NowMono
                time.sleep(min(1, max(0, Window["planned_until"] - time.time())))
            ReturnCode = Owner.Process.poll()
        finally:
            Owner.CloseOwner()
        if time.time() >= Window["planned_until"]:
            AppendEvent(Directory, "window_complete", launches=Attempts)
            return 0
        AppendEvent(
            Directory,
            "supervisor_exited",
            returncode=ReturnCode,
            stale=Stale,
            attempt=Attempts,
        )
        if ReturnCode == 4:
            AppendEvent(
                Directory,
                "circuit_open",
                reason="supervisor_owner_busy",
                launches=Attempts,
            )
            return 2
        DelaySecs = min(60, 2 ** min(Attempts, 6))
        AppendEvent(Directory, "restart_wait", seconds=DelaySecs)
        ResumeAt = min(Window["planned_until"], time.time() + DelaySecs)
        while (
            time.time() < ResumeAt
            and not IsStopping()
            and not (Directory / "Stop.request").exists()
        ):
            time.sleep(min(1, max(0, ResumeAt - time.time())))
    AppendEvent(Directory, "window_complete", launches=Attempts)
    return 0
