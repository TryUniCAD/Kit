# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import time

from Records import bounded, digest, label
from SharedQueue.Lifecycle import reconcile_members
from SharedQueue.Plan import canonical_jobs, request_plan
from SharedQueue.State import initialize, pending_count


# exact revision matching makes retries harmless and rejects stale request replacement
def check_revision(previous, revision, payload_hash, active):
    if previous is None:
        return False
    if revision < previous["revision"]:
        raise ValueError("shared request revision is stale")
    if revision == previous["revision"]:
        if (
            previous["payload_hash"] != payload_hash
            or bool(previous["active"]) != active
        ):
            raise ValueError(
                "same shared request revision has different content or cancellation state"
            )
        return True
    return False


# equivalent workflow definitions share one execution while each client retains its subscription
def enqueue(ledger, value):
    plan = request_plan(value)
    initialize(ledger)
    previous = ledger.db.execute(
        "SELECT * FROM shared_requests WHERE request=?", (plan["request"],)
    ).fetchone()
    payload_hash = digest(plan)
    idempotent = check_revision(previous, plan["revision"], payload_hash, True)
    aliases, specs = canonical_jobs(plan["jobs"])
    known = {
        spec["id"]
        for spec in specs
        if ledger.db.execute(
            "SELECT 1 FROM shared_jobs WHERE job_id=?", (spec["id"],)
        ).fetchone()
        is not None
    }
    previous_members = {
        row[0]
        for row in ledger.db.execute(
            "SELECT job_id FROM shared_members WHERE request=?", (plan["request"],)
        )
    }
    ledger.submit_many(specs, reconcile_shared=False)
    ledger.db.executemany(
        "INSERT OR IGNORE INTO shared_jobs VALUES (?)",
        ((spec["id"],) for spec in specs),
    )
    ledger.db.execute(
        "INSERT INTO shared_requests VALUES (?,?,?,?,?,?) ON CONFLICT(request) DO UPDATE SET revision=excluded.revision,payload_hash=excluded.payload_hash,active=excluded.active,priority=excluded.priority,updated=excluded.updated",
        (
            plan["request"],
            plan["revision"],
            payload_hash,
            1,
            plan["priority"],
            time.time(),
        ),
    )
    if (
        ledger.db.execute(
            "SELECT value FROM settings WHERE key='shared_request_count'"
        ).fetchone()[0]
        > 10000
    ):
        raise ValueError("shared request metadata limit exceeded")
    ledger.db.execute("DELETE FROM shared_members WHERE request=?", (plan["request"],))
    ledger.db.executemany(
        "INSERT INTO shared_members VALUES (?,?,?)",
        ((plan["request"], local_id, job_id) for local_id, job_id in aliases.items()),
    )
    if (
        ledger.db.execute(
            "SELECT value FROM settings WHERE key='shared_subscription_count'"
        ).fetchone()[0]
        > 100000
    ):
        raise ValueError("shared subscription metadata limit exceeded")
    cancelled = reconcile_members(ledger, previous_members | set(aliases.values()))
    reused = {
        spec["id"]
        for spec in specs
        if ledger.db.execute(
            "SELECT 1 FROM jobs WHERE id=? AND state='completed'", (spec["id"],)
        ).fetchone()
        is not None
    }
    maximum = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_max_pending'"
    ).fetchone()[0]
    if pending_count(ledger) > maximum:
        raise ValueError("shared pending queue limit exceeded")
    ledger.event(
        None,
        "shared_enqueued",
        {
            "request": plan["request"],
            "revision": plan["revision"],
            "unique_jobs": len(specs),
            "shared_jobs": len(known),
            "reused_jobs": len(reused),
            "cancelled_jobs": cancelled,
        },
    )
    return {
        "request": plan["request"],
        "revision": plan["revision"],
        "active": True,
        "jobs": aliases,
        "shared_jobs": len(known),
        "reused_jobs": len(reused),
        "idempotent": idempotent,
        "shared_reconciled_jobs": ledger.shared_reconciled,
        "shared_reconcile_passes": ledger.shared_reconcile_passes,
    }


# cancellation requires an explicit newer revision so late clients cannot stop replacement work
def cancel(ledger, request, revision):
    request, revision = label(request), bounded(revision, 0, 2**63 - 1)
    initialize(ledger)
    previous = ledger.db.execute(
        "SELECT * FROM shared_requests WHERE request=?", (request,)
    ).fetchone()
    if previous is None:
        raise ValueError("unknown shared request")
    payload_hash = digest({"request": request, "revision": revision, "active": False})
    idempotent = check_revision(previous, revision, payload_hash, False)
    ledger.db.execute(
        "UPDATE shared_requests SET revision=?,payload_hash=?,active=0,updated=? WHERE request=?",
        (revision, payload_hash, time.time(), request),
    )
    members = {
        row[0]
        for row in ledger.db.execute(
            "SELECT job_id FROM shared_members WHERE request=?", (request,)
        )
    }
    cancelled = reconcile_members(ledger, members)
    ledger.event(
        None,
        "shared_request_cancelled",
        {"request": request, "revision": revision, "cancelled_jobs": cancelled},
    )
    return {
        "request": request,
        "revision": revision,
        "active": False,
        "cancelled_jobs": cancelled,
        "idempotent": idempotent,
        "shared_reconciled_jobs": ledger.shared_reconciled,
        "shared_reconcile_passes": ledger.shared_reconcile_passes,
    }
