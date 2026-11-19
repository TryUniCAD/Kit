# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep

from InferenceGrid.Evidence import KScopeGap
from InferenceGrid.Resume import AttachQueuedGrid, ParkedGrid, ReadAttachedGrid
from Ledger import Ledger
from PairedCaptureIntake import require
from PairedCaptures.ScopeControl.FusionScopeControl import prepare
from QueueFusionPhases import bind_pair, prepare_pair, queue_configuration
from Records import digest

# the catalogue route keeps the existing assessment identity and dependencies
ScopeJob = "inference:" + digest(KScopeGap)


# retries read the already attached controller evidence instead of queueing another experiment
def ReadAssessment(ledger):
    records = ledger.status(ScopeJob)["jobs"]
    require(records, "submit the cut-extrude feature before advancing its evidence")
    row = ledger.db.execute("SELECT * FROM jobs WHERE id=?", (ScopeJob,)).fetchone()
    definition = json.loads(row["definition"])
    reply = {"assessment": records[0], "phase_jobs": {}}
    if "grid_from_receipt" in definition["options"]:
        queue, _ = ReadAttachedGrid(ledger, definition)
        reply.update(status="experiment_attached", phase_jobs=queue["jobs"])
    elif row["state"] == "waiting_evidence" and row["parked"]:
        ParkedGrid(ledger, row, row["receipt"])
        reply["status"] = "experiment_needed"
    else:
        reply["status"] = "awaiting_assessment"
    return reply, definition


# the evidence decision and both phase submissions become visible together
def QueueEvidence(store, configuration, kind, resource, origin, revision):
    configured_store, installation, acknowledgement = queue_configuration(
        configuration, kind, resource
    )
    require(
        configured_store.resolve(strict=True) == store,
        "Fusion runner uses another controller store",
    )
    require(
        installation["source_revision"] == revision,
        "Fusion runner uses another source revision",
    )
    with TemporaryDirectory(prefix="kit-feature-evidence-") as temporary:
        scratch = Path(temporary)
        prepared = scratch / "Prepared"
        prepare(prepared)
        raw = (prepared / "plan.json").read_bytes()
        receipt, jobs = prepare_pair(
            installation,
            acknowledgement,
            kind,
            resource,
            "feature-" + origin,
            scratch / "plan.json",
            raw,
        )
        verification = scratch / "Verification"
        verification.mkdir()
        with Ledger(store) as ledger:
            reply, _ = ReadAssessment(ledger)
            if reply["status"] == "experiment_attached":
                return reply
            require(
                reply["status"] == "experiment_needed"
                and reply["assessment"]["receipt"] == origin,
                "the assessment changed while preparing the evidence experiment",
            )
            bind_pair(ledger, scratch / "plan.json", receipt, jobs, durable=True)
            AttachQueuedGrid(ledger, store, receipt, origin, verification)
            return ReadAssessment(ledger)[0]


# a bounded wait lets an operator start the handoff before the assessment settles
def AdvanceEvidence(store, configuration, kind, resource, wait_seconds):
    store = store.resolve(strict=True)
    deadline = monotonic() + wait_seconds
    while True:
        with Ledger(store) as ledger:
            reply, definition = ReadAssessment(ledger)
        if reply["status"] == "experiment_needed":
            return QueueEvidence(
                store,
                configuration,
                kind,
                resource,
                reply["assessment"]["receipt"],
                definition["tool_version"],
            )
        if (
            reply["status"] != "awaiting_assessment"
            or reply["assessment"]["state"] not in {"queued", "running"}
            or monotonic() >= deadline
        ):
            return reply
        sleep(min(1, max(0, deadline - monotonic())))
