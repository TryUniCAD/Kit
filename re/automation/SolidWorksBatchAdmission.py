# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import time

# the optional table leaves stores that never use batch admission on their original claim path
TableName = "solidworks_batch_admission"


# a short expiry allows other jobs to proceed if the watcher is stopped abruptly
def PrepareAdmission(Db):
    Db.execute(
        "CREATE TABLE IF NOT EXISTS solidworks_batch_admission ("
        "resource TEXT PRIMARY KEY, installation TEXT NOT NULL, "
        "expires REAL NOT NULL, batch_id TEXT REFERENCES jobs(id), definition_hash TEXT)"
    )


# both claim paths consult the same reservation for the exact queued batch and resource
def ClaimExclusion(Job):
    return f"""EXISTS (
        SELECT 1 FROM solidworks_batch_admission hold
        JOIN job_resources r ON r.resource=hold.resource
        WHERE r.job_id={Job}.id AND hold.expires>:now
        AND (
            hold.batch_id IS NULL OR EXISTS (
                SELECT 1 FROM jobs batch
                WHERE batch.id=hold.batch_id AND batch.definition_hash=hold.definition_hash
                  AND batch.state IN ('queued','running')
            )
        )
        AND (hold.batch_id IS NULL OR {Job}.id<>hold.batch_id)
    )"""


# the claim code supports ledgers created before automatic readback was introduced
def IsAdmissionInstalled(Ledger):
    return (
        Ledger.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TableName,)
        ).fetchone()
        is not None
    )


# a reservation follows the installation until its selected batch has been submitted
def ReserveAdmission(Db, Resource, Identity, Seconds):
    Db.execute(
        "INSERT INTO solidworks_batch_admission VALUES (?, ?, ?, NULL, NULL) "
        "ON CONFLICT(resource) DO UPDATE SET installation=excluded.installation, expires=excluded.expires, "
        "batch_id=CASE WHEN solidworks_batch_admission.installation=excluded.installation THEN batch_id END, "
        "definition_hash=CASE WHEN solidworks_batch_admission.installation=excluded.installation THEN definition_hash END "
        "WHERE solidworks_batch_admission.installation=excluded.installation "
        "OR solidworks_batch_admission.expires<=?",
        (Resource, Identity, time.time() + Seconds, time.time()),
    )


# associating the job releases admission automatically when that exact job stops running
def AttachBatch(Db, Resource, Identity, Job, DefinitionHash):
    Db.execute(
        "UPDATE solidworks_batch_admission SET batch_id=?, definition_hash=? "
        "WHERE resource=? AND installation=?",
        (Job, DefinitionHash, Resource, Identity),
    )


# an expired or terminal batch must not retain admission over a new cohort
def IsReserved(Db, Resource, Identity):
    return (
        Db.execute(
            "SELECT 1 FROM solidworks_batch_admission "
            "WHERE resource=? AND installation=? AND expires>? AND batch_id IS NULL",
            (Resource, Identity, time.time()),
        ).fetchone()
        is not None
    )


# a quick batch may settle between watcher polls without ever being observed as active
def HasAttachedBatch(Db, Resource, Identity):
    return (
        Db.execute(
            "SELECT 1 FROM solidworks_batch_admission "
            "WHERE resource=? AND installation=? AND batch_id IS NOT NULL",
            (Resource, Identity),
        ).fetchone()
        is not None
    )


# a clean watcher shutdown returns admission immediately
def ReleaseAdmission(Db, Resource, Identity):
    Db.execute(
        "DELETE FROM solidworks_batch_admission WHERE resource=? AND installation=?",
        (Resource, Identity),
    )
