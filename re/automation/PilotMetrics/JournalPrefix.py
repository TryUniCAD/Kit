# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from hashlib import sha256 as ShaDigest
from json import loads as LoadJson
from math import isfinite as IsFinite

from ReadRun import UniqueObject


# the live append journal must be cut at complete records before it can be replayed
def JournalPrefix(FilePath, StartTime, UntilTime, RunName):
    if FilePath.is_symlink() or not FilePath.is_file():
        raise ValueError("pilot journal must be a regular nonsymlink file")
    Content = bytearray()
    Previous = 0.0
    Records = []
    with FilePath.open("rb") as SourceFile:
        for LineBytes in SourceFile:
            if not LineBytes.endswith(b"\n"):
                break
            if len(LineBytes) > 1024 * 1024:
                raise ValueError("pilot journal record exceeds 1 MiB")
            Record = LoadJson(LineBytes, object_pairs_hook=UniqueObject)
            if not isinstance(Record, dict):
                raise ValueError("pilot journal record must be an object")
            Instant = Record.get("at")
            if (
                type(Instant) not in (int, float)
                or not IsFinite(Instant)
                or Instant < Previous
                or not isinstance(Record.get("event"), str)
                or Record.get("run_id") != RunName
            ):
                raise ValueError(
                    "pilot journal must contain chronological typed records"
                )
            Previous = Instant
            if Instant >= UntilTime:
                break
            Content.extend(LineBytes)
            if Instant >= StartTime:
                Records.append(Record)
    Counts = dict(sorted(Counter(Record["event"] for Record in Records).items()))
    Heartbeats = [Record for Record in Records if Record["event"] == "heartbeat"]
    Times = [StartTime, *(Record["at"] for Record in Records), UntilTime]
    HealthyTimes = [
        StartTime,
        *(
            Record["at"]
            for Record in Heartbeats
            if Record.get("supervisor_healthy") is True
        ),
        UntilTime,
    ]
    return bytes(Content), {
        "journal_prefix_sha256": ShaDigest(Content).hexdigest(),
        "selected_records": len(Records),
        "event_counts": Counts,
        "last_observation_at": Records[-1]["at"] if Records else None,
        "seconds_after_last_observation": (
            UntilTime - Records[-1]["at"] if Records else None
        ),
        "max_seconds_between_observations_including_boundaries": max(
            Right - Left for Left, Right in zip(Times, Times[1:])
        ),
        "healthy_supervisor_heartbeat_samples": sum(
            Record.get("supervisor_healthy") is True for Record in Heartbeats
        ),
        "unhealthy_supervisor_heartbeat_samples": sum(
            Record.get("supervisor_healthy") is False for Record in Heartbeats
        ),
        "unmeasured_supervisor_heartbeat_samples": sum(
            type(Record.get("supervisor_healthy")) is not bool for Record in Heartbeats
        ),
        "coverage": "recorded_events_only",
        "max_seconds_between_healthy_supervisor_samples_including_boundaries": max(
            Right - Left for Left, Right in zip(HealthyTimes, HealthyTimes[1:])
        ),
    }
