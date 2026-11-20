# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from tempfile import TemporaryDirectory

from InferenceGrid.Provision import CheckRevision, HasScopePlan
from InferenceGrid.Resume import BindGrid
from Ledger import Ledger
from PairedCaptureIntake import require, sha256
from PrioritySchedule import schedule
from Records import digest


# shared discovery routes preserve exact bindings and assessment identities
def ProvisionAssessment(Store, Revision, CaptureRevision, BuildSchedule):
    CheckRevision(Revision)
    Bindings, Batch = BuildSchedule(Revision)
    Jobs = Batch["jobs"]
    with (
        TemporaryDirectory(prefix="kit-feature-provision-") as Scratch,
        Ledger(Store) as State,
    ):
        Exists = HasScopePlan(State, Batch)
        for Name, Raw in sorted(Bindings.items()):
            Pin = sha256(Raw)
            Staged = Path(Scratch) / Pin
            Staged.write_bytes(Raw)
            require(
                State.objects.put_file(Staged) == Pin,
                "stored feature input differs from its pin",
            )
            BindGrid(State, Name, Pin)
        if not Exists:
            schedule(State, Batch)
        return {
            "scope": Jobs[0]["options"]["scope"],
            "source_revision": Revision,
            "capture_revision": CaptureRevision,
            "assessment_job": Jobs[0]["id"],
            "jobs": [State.status(Job["id"])["jobs"][0] for Job in Jobs],
        }


# related catalogue entries can read the same assessment and dependent rescans
def ReadFeatureAssessment(State, Scope):
    Job = "inference:" + digest(Scope)
    Results = State.status(Job)["jobs"]
    require(Results, "submit this feature assessment before reading its status")
    Rows = State.db.execute(
        "SELECT j.id FROM dependencies d JOIN jobs j ON j.id=d.job_id "
        "WHERE d.dependency=? AND j.kind='inference.rescan' ORDER BY j.id",
        (Job,),
    ).fetchall()
    return {
        "assessment": Results[0],
        "rescans": [State.status(Row[0])["jobs"][0] for Row in Rows],
    }
