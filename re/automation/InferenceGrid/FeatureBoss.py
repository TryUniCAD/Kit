# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from tempfile import TemporaryDirectory

from InferenceArchives import REVISION, archive_cases
from InferenceGrid.Provision import CheckRevision, HasScopePlan
from InferenceGrid.Resume import BindGrid
from InferenceSchedule import build_schedule
from Ledger import Ledger
from PairedCaptureIntake import require, sha256
from PrioritySchedule import schedule
from Records import canonical, digest

# assessments and rescans retain the job identities used by the offline pilot
BossScope = "p03-blind-boss.solidworks"


# pinned discovery archives provide a real decoder route for the shared planner
def BossSchedule(Revision):
    ((Plan, Streams, Archives),) = archive_cases(("solidworks",))
    require(Plan["scope"] == BossScope, "P03 plan differs from the reviewed boss scope")
    PlanName = BossScope + ":plan"
    Bindings = {PlanName: canonical(Plan).encode("utf-8"), **Streams}
    require(
        not (set(Bindings) & Archives.keys()),
        "P03 archive binding collides with a stream",
    )
    for Pin, (_, Raw) in Archives.items():
        require(sha256(Raw) == Pin, "P03 archive differs from its capture pin")
        Bindings[Pin] = Raw
    Batch = build_schedule(
        {
            "inference_version": 1,
            "scope": BossScope,
            "family": "rectangular-history",
            "rule_version": "archive-field-search@1",
            "tool_version": "offline-pilot@" + Revision,
            "plan_input": PlanName,
            "stream_inputs": {Role: Role for Role in sorted(Streams)},
            "archives": {
                Pin: {"format": Format, "binding": Pin}
                for Pin, (Format, _) in sorted(Archives.items())
            },
            "distinguishing_evidence": [
                "direction-negative",
                "depth-edit",
                "width-edit",
                "height-edit",
            ],
            "depends_on": [],
        }
    )
    return Bindings, Batch


# all source objects and jobs are published in one store transaction
def ProvisionBoss(Store, Revision):
    CheckRevision(Revision)
    Bindings, Batch = BossSchedule(Revision)
    with (
        TemporaryDirectory(prefix="kit-boss-provision-") as Scratch,
        Ledger(Store) as State,
    ):
        Exists = HasScopePlan(State, Batch)
        for Name, Raw in sorted(Bindings.items()):
            Pin = sha256(Raw)
            PathValue = Path(Scratch) / Pin
            PathValue.write_bytes(Raw)
            require(
                State.objects.put_file(PathValue) == Pin,
                "stored P03 input differs from its pin",
            )
            BindGrid(State, Name, Pin)
        if not Exists:
            schedule(State, Batch)
        return {
            "scope": BossScope,
            "source_revision": Revision,
            "capture_revision": REVISION,
            "assessment_job": Batch["jobs"][0]["id"],
            "jobs": [State.status(Job["id"])["jobs"][0] for Job in Batch["jobs"]],
        }


# status follows only the rescans that depend on this specific boss assessment
def ReadBoss(State):
    Job = "inference:" + digest(BossScope)
    Records = State.status(Job)["jobs"]
    require(Records, "submit the boss-base-extrude feature before reading its status")
    Rows = State.db.execute(
        "SELECT j.id FROM dependencies d JOIN jobs j ON j.id=d.job_id "
        "WHERE d.dependency=? AND j.kind='inference.rescan' ORDER BY j.id",
        (Job,),
    ).fetchall()
    return {
        "assessment": Records[0],
        "rescans": [State.status(Row[0])["jobs"][0] for Row in Rows],
    }
