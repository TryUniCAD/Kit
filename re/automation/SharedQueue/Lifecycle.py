# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from SharedQueue.State import installed


# cancellation fences running leases while preserving accepted evidence for later subscribers
def reconcile_cancelled(ledger, row):
    if (
        not installed(ledger)
        or ledger.db.execute(
            "SELECT 1 FROM shared_cancelled WHERE job_id=?", (row["id"],)
        ).fetchone()
        is None
    ):
        return False
    if row["state"] == "completed":
        ledger.verify_object(row["receipt"])
        ledger.verify_result(row["result"])
        return True
    if row["state"] != "rejected" or row["reason"] != "shared request superseded":
        receipt = ledger.revoke(row, "invalidated")
        ledger.db.execute(
            "UPDATE jobs SET state='rejected',parked=1,receipt=?,result=NULL,reason='shared request superseded' WHERE id=?",
            (receipt, row["id"]),
        )
        ledger.enqueue_children(row["id"])
        ledger.event(
            row["id"],
            "shared_cancelled",
            {"reason": "no remaining subscribers or dependent jobs"},
        )
    return True


# active subscribers and external dependents retain the entire shared prerequisite closure
def reconcile_members(ledger):
    needed = {
        row[0]
        for row in ledger.db.execute(
            "WITH RECURSIVE needed(id) AS ("
            "SELECT m.job_id FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 "
            "UNION SELECT d.dependency FROM dependencies d LEFT JOIN shared_jobs s ON s.job_id=d.job_id WHERE s.job_id IS NULL "
            "UNION SELECT d.dependency FROM dependencies d JOIN needed n ON n.id=d.job_id) SELECT id FROM needed"
        )
    }
    shared = {row[0] for row in ledger.db.execute("SELECT job_id FROM shared_jobs")}
    cancelled = {
        row[0] for row in ledger.db.execute("SELECT job_id FROM shared_cancelled")
    }
    for job_id in sorted(shared - needed - cancelled):
        ledger.db.execute("INSERT INTO shared_cancelled VALUES (?)", (job_id,))
        ledger.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (job_id,))
    for job_id in sorted(cancelled & needed):
        ledger.db.execute("DELETE FROM shared_cancelled WHERE job_id=?", (job_id,))
        ledger.db.execute(
            "UPDATE jobs SET parked=0,state='queued',reason=NULL WHERE id=? AND state='rejected' AND reason='shared request superseded'",
            (job_id,),
        )
        ledger.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (job_id,))
        ledger.event(job_id, "shared_restored", {})
    ledger.refresh()
    return len(shared - needed - cancelled)
