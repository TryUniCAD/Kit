# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from graphlib import CycleError, TopologicalSorter

from SharedQueue.State import installed
from SharedQueue.Demand import install_demand
from SharedQueue.Stats import install_report


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
    install_report(ledger)
    install_demand(ledger)
    pending, closure, upstream = set(roots), set(), {}
    while pending:
        job_id = pending.pop()
        if job_id in closure:
            continue
        closure.add(job_id)
        upstream[job_id] = {
            row[0]
            for row in ledger.db.execute(
                "SELECT dependency FROM dependencies WHERE job_id=?", (job_id,)
            )
        }
        pending.update(upstream[job_id])
    candidates = {}
    for job_id in closure:
        row = ledger.db.execute(
            "SELECT s.job_id,c.job_id AS cancelled FROM shared_jobs s LEFT JOIN shared_cancelled c ON c.job_id=s.job_id WHERE s.job_id=?",
            (job_id,),
        ).fetchone()
        if row is not None:
            candidates[job_id] = row["cancelled"] is not None
    graph = {job_id: set() for job_id in candidates}
    for child, parents in upstream.items():
        if child in candidates:
            for parent in parents:
                if parent in candidates:
                    graph[parent].add(child)
    try:
        order = tuple(TopologicalSorter(graph).static_order())
    except CycleError as error:
        raise ValueError(
            "shared prerequisite graph contains a dependency cycle"
        ) from error
    cancelled = 0
    for job_id in order:
        active_refs = ledger.db.execute(
            "SELECT active_refs FROM shared_report_items WHERE job_id=?", (job_id,)
        ).fetchone()[0]
        demand = ledger.db.execute(
            "SELECT live_children FROM shared_demand WHERE dependency=?", (job_id,)
        ).fetchone()
        needed = active_refs > 0 or (demand is not None and demand[0] > 0)
        if not needed and not candidates[job_id]:
            ledger.db.execute("INSERT INTO shared_cancelled VALUES (?)", (job_id,))
            ledger.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (job_id,))
            cancelled += 1
        elif needed and candidates[job_id]:
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
