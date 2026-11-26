# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from ControllerFacts import ControllerFacts
from JournalPrefix import JournalPrefix
from PilotActivity import operating_report as OperatingReport
from PilotEvidence import report as EvidenceReport
from ReadRun import ReadObject, ReadRun


# actual elapsed operating time stays separate from the planned duration and acceptance authority
def BuildReport(BundleRoot, Snapshot, StorePath):
    Manifest, Observe, ManifestHash, ObserveHash = ReadRun(BundleRoot)
    StartTime = Observe["started_at"]
    UntilTime = Snapshot["until_unix_seconds"]
    Activity = OperatingReport(
        StorePath,
        StartTime,
        UntilTime,
        0,
        Snapshot["through_event_id"],
        time_dependencies=True,
        time_waits=True,
        time_open_waits=True,
        time_carry_in_waits=True,
    )
    _, Watchdog = JournalPrefix(
        BundleRoot / "Events.jsonl", StartTime, UntilTime, Manifest["run_id"]
    )
    Private = None
    if "evidence_manifest_sha256" in Snapshot:
        Private = EvidenceReport(
            StorePath,
            BundleRoot / "Evidence" / "PilotEvidence.json",
            Snapshot["evidence_manifest_sha256"],
        )
        for Field in (
            "from_unix_seconds",
            "until_unix_seconds",
            "after_event_id",
            "through_event_id",
            "selected_events_sha256",
        ):
            if Private["controller_activity"][Field] != Activity[Field]:
                raise ValueError("private evidence must bind this exact report window")
    Completed = Activity["activity"]["settled_outcomes"]["completed"]
    Provisional = Activity["activity"]["provisional_completions"]
    Elapsed = UntilTime - StartTime
    QueueState = (
        ReadObject(BundleRoot / "JobSnapshot.json")[0]
        if (BundleRoot / "JobSnapshot.json").is_file()
        else {"status": "unavailable_at_historical_cutoff"}
    )
    CompletedJobs = {
        Job["id"] for Job in QueueState.get("jobs", []) if Job["state"] == "completed"
    }
    return {
        "report_version": 1,
        "scope": "a15a_offline_pilot_observation",
        "run_id": Manifest["run_id"],
        "source_revision": Manifest["source_revision"],
        "run_manifest_sha256": ManifestHash,
        "observation_sha256": ObserveHash,
        "model_calls_enabled": False,
        "application_dispatch_enabled": False,
        "observation": {
            "started_at": StartTime,
            "observed_until": UntilTime,
            "planned_until": Observe["planned_until"],
            "observed_seconds": Elapsed,
            "required_seconds": 1209600,
            "window_status": (
                "elapsed" if UntilTime >= Observe["planned_until"] else "in_progress"
            ),
            "pilot_acceptance": "outstanding_independent_evidence_review",
        },
        "throughput": {
            "settled_completed_attempts": Completed,
            "nonprovisional_completed_attempts": Completed - Provisional,
            "completed_attempts_per_observed_hour": Completed * 3600 / Elapsed,
            "document_gain_inferred_from_completion": False,
            "completed_jobs_at_queue_observation": (
                len(CompletedJobs) if "jobs" in QueueState else None
            ),
        },
        "controller_activity": Activity,
        "controller_facts": ControllerFacts(
            StorePath, StartTime, UntilTime, Activity["through_event_id"]
        ),
        "queue_observation": QueueState,
        "watchdog": Watchdog,
        "independent_evidence": Private
        or {
            "interventions": {"status": "unmeasured"},
            "agent_activity": {"status": "unmeasured"},
            "acceptance": {"status": "unmeasured", "verified_gains_claimed": 0},
        },
        "limitations": [
            "watchdog heartbeats do not prove uninterrupted host or worker availability",
            "controller attempt time does not measure active agent time",
            "attestation schemas and hashes do not independently verify referenced acceptance receipts",
            "definition_changed transitions do not reconstruct dependency-only queue parking",
            "offline execution establishes no native conversion qualification",
        ],
    }
