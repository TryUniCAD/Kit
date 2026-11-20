# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from json import loads as LoadJson

from Artifacts import Artifacts
from EventHistory import event_window as EventWindow
from ResourceOccupancy import stored_record as StoredRecord


# replayed transitions preserve parked evidence without refreshing or mutating current jobs
def ControllerFacts(StorePath, StartTime, UntilTime, Through):
    JobStates = {}
    ClaimStarts = {}
    ClosedSeconds = 0.0
    ClosedClaims = 0
    Cursor = 0
    while True:
        PageInfo = EventWindow(StorePath, None, Cursor, Through)
        for Event in PageInfo["events"]:
            if Event["at"] >= UntilTime or Event["job_id"] is None:
                continue
            Detail = LoadJson(Event["detail"])
            JobName = Event["job_id"]
            Action = Event["action"]
            if Action == "claimed":
                ClaimStarts[JobName] = Event["at"]
                JobStates[JobName] = {"state": "running", "event_id": Event["id"]}
            elif Action in ("submitted", "invalidated"):
                JobStates[JobName] = {
                    "state": "definition_changed",
                    "event_id": Event["id"],
                }
                ClaimStarts.pop(JobName, None)
            elif Action in ("finished", "expired"):
                Started = ClaimStarts.pop(JobName, None)
                if Started is not None and Event["at"] >= StartTime:
                    ClosedSeconds += Event["at"] - max(Started, StartTime)
                    ClosedClaims += 1
                JobStates[JobName] = {**Detail, "event_id": Event["id"]}
        Cursor = PageInfo["next_after"]
        if Cursor is None:
            break
    Objects = Artifacts(StorePath, create=False)
    Parked = []
    for JobName, State in sorted(JobStates.items()):
        if State["state"] in ("waiting_evidence", "waiting_ci", "waiting_application"):
            Receipt = StoredRecord(Objects, State["receipt"])
            if Receipt["job_id"] != JobName or Receipt["outcome"] != State["outcome"]:
                raise ValueError("parked receipt differs from historical settlement")
            Parked.append({"job": JobName, **State, "reason": Receipt["reason"]})
    return {
        "scope": "last_recorded_job_transitions_not_current_queue_status",
        "states": dict(
            sorted(Counter(State["state"] for State in JobStates.values()).items())
        ),
        "parked_jobs": Parked,
        "closed_attempts_with_observed_claim": ClosedClaims,
        "closed_attempt_wall_seconds": ClosedSeconds,
        "agent_time_attribution": "requires_independent_agent_intervals",
    }
