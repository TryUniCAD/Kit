# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from graphlib import CycleError, TopologicalSorter

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


# changed subscriptions can affect only their own upstream prerequisites
def reconcile_members(ledger, roots):
    pending, closure = set(roots), set()
    while pending:
        job_id = pending.pop()
        if job_id in closure:
            continue
        closure.add(job_id)
        pending.update(
            row[0]
            for row in ledger.db.execute(
                "SELECT dependency FROM dependencies WHERE job_id=?", (job_id,)
            )
        )
    candidates = {}
    for job_id in closure:
        row = ledger.db.execute(
            "SELECT s.job_id,c.job_id AS cancelled FROM shared_jobs s LEFT JOIN shared_cancelled c ON c.job_id=s.job_id WHERE s.job_id=?",
            (job_id,),
        ).fetchone()
        if row is not None:
            candidates[job_id] = row["cancelled"] is not None
    graph, direct = {}, {}
    for job_id in candidates:
        children = ledger.db.execute(
            "SELECT d.job_id,s.job_id AS shared,c.job_id AS cancelled FROM dependencies d LEFT JOIN shared_jobs s ON s.job_id=d.job_id LEFT JOIN shared_cancelled c ON c.job_id=d.job_id WHERE d.dependency=?",
            (job_id,),
        ).fetchall()
        graph[job_id] = {
            row["job_id"] for row in children if row["job_id"] in candidates
        }
        direct[job_id] = ledger.db.execute(
            "SELECT 1 FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE m.job_id=? AND r.active=1 LIMIT 1",
            (job_id,),
        ).fetchone() is not None or any(
            row["shared"] is None
            or (row["job_id"] not in candidates and row["cancelled"] is None)
            for row in children
        )
    try:
        order = tuple(TopologicalSorter(graph).static_order())
    except CycleError as error:
        raise ValueError(
            "shared prerequisite graph contains a dependency cycle"
        ) from error
    needed, cancelled = {}, 0
    for job_id in order:
        needed[job_id] = direct[job_id] or any(needed[child] for child in graph[job_id])
        if not needed[job_id] and not candidates[job_id]:
            ledger.db.execute("INSERT INTO shared_cancelled VALUES (?)", (job_id,))
            ledger.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (job_id,))
            cancelled += 1
        elif needed[job_id] and candidates[job_id]:
            ledger.db.execute("DELETE FROM shared_cancelled WHERE job_id=?", (job_id,))
            ledger.db.execute(
                "UPDATE jobs SET parked=0,state='queued',reason=NULL WHERE id=? AND state='rejected' AND reason='shared request superseded'",
                (job_id,),
            )
            ledger.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (job_id,))
            ledger.event(job_id, "shared_restored", {})
    ledger.shared_reconciled = getattr(ledger, "shared_reconciled", 0) + len(closure)
    ledger.shared_reconcile_passes = getattr(ledger, "shared_reconcile_passes", 0) + 1
    ledger.event(
        None,
        "shared_members_reconciled",
        {"examined_jobs": len(closure), "shared_jobs": len(candidates)},
    )
    ledger.refresh()
    return cancelled
