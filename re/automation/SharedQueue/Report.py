# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import time

from Records import label
from SharedQueue.State import installed
from SharedQueue.Stats import install_report


# clients need bounded subscription summaries without reading private leases
def queue_status(ledger, request=None, after=None):
    if request is not None:
        request = label(request)
    if after is not None:
        after = label(after)
    if not installed(ledger):
        return {
            "queue_version": 1,
            "scope": "queue_metadata",
            "acceptance_verified": False,
            "artifact_bytes_hashed": ledger.bytes_hashed,
            "max_pending": 1000,
            "requests": [],
            "next_after": None,
            "subscriptions": 0,
            "unique_jobs": 0,
            "pending_jobs": 0,
            "shared_jobs": 0,
            "reused_jobs": 0,
            "cancelled_jobs": 0,
            "states": {},
            "oldest_queued_seconds": 0,
        }
    install_report(ledger)
    if request is None:
        rows = ledger.db.execute(
            "SELECT r.*,p.job_count FROM shared_requests r JOIN shared_report_requests p ON p.request=r.request WHERE r.request>? ORDER BY r.request LIMIT 101",
            (after or "",),
        ).fetchall()
    else:
        rows = ledger.db.execute(
            "SELECT r.*,p.job_count FROM shared_requests r JOIN shared_report_requests p ON p.request=r.request WHERE r.request=? AND r.request>?",
            (request, after or ""),
        ).fetchall()
    requests = []
    for row in rows[:100]:
        summary = {
            "request": row["request"],
            "revision": row["revision"],
            "active": bool(row["active"]),
            "priority": row["priority"],
            "job_count": row["job_count"],
        }
        if request is not None:
            summary["jobs"] = {
                member["local_id"]: member["job_id"]
                for member in ledger.db.execute(
                    "SELECT local_id,job_id FROM shared_members WHERE request=? ORDER BY local_id",
                    (row["request"],),
                )
            }
        requests.append(summary)
    if request is None:
        totals = dict(ledger.db.execute("SELECT name,value FROM shared_report_totals"))
        states = dict(
            ledger.db.execute(
                "SELECT state,count FROM shared_report_states WHERE count>0"
            )
        )
        counts = (totals["subscriptions"], totals["active_jobs"])
        unique_count = sum(states.values())
        oldest_row = ledger.db.execute(
            "SELECT created FROM shared_report_items WHERE cancelled=0 AND state='queued' ORDER BY created,job_id LIMIT 1"
        ).fetchone()
        oldest = oldest_row[0] if oldest_row is not None else time.time()
        cancelled = totals["cancelled_jobs"]
    else:
        active = ledger.db.execute(
            "SELECT active FROM shared_requests WHERE request=?", (request,)
        ).fetchone()
        if active is not None and active[0]:
            counts = ledger.db.execute(
                "SELECT COUNT(*),COUNT(DISTINCT job_id) FROM shared_members WHERE request=?",
                (request,),
            ).fetchone()
            unique = ledger.db.execute(
                "SELECT DISTINCT j.id,j.state,j.created FROM shared_members m JOIN jobs j ON j.id=m.job_id WHERE m.request=?",
                (request,),
            ).fetchall()
        else:
            counts, unique = (0, 0), []
        unique_count = len(unique)
        states = {}
        for row in unique:
            states[row["state"]] = states.get(row["state"], 0) + 1
        oldest = min(
            (row["created"] for row in unique if row["state"] == "queued"),
            default=time.time(),
        )
        cancelled = ledger.db.execute(
            "SELECT COUNT(DISTINCT m.job_id) FROM shared_members m JOIN shared_cancelled c ON c.job_id=m.job_id WHERE m.request=?",
            (request,),
        ).fetchone()[0]
    maximum = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_max_pending'"
    ).fetchone()[0]
    return {
        "queue_version": 1,
        "scope": "queue_metadata",
        "acceptance_verified": False,
        "artifact_bytes_hashed": ledger.bytes_hashed,
        "max_pending": maximum,
        "requests": requests,
        "next_after": rows[99]["request"] if len(rows) > 100 else None,
        "subscriptions": counts[0],
        "unique_jobs": unique_count,
        "pending_jobs": sum(
            count
            for state, count in states.items()
            if state
            in {
                "queued",
                "running",
                "waiting_evidence",
                "waiting_application",
                "waiting_ci",
            }
        ),
        "shared_jobs": counts[0] - counts[1],
        "reused_jobs": states.get("completed", 0),
        "cancelled_jobs": cancelled,
        "states": states,
        "oldest_queued_seconds": max(0, time.time() - oldest),
    }
