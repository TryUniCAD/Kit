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
    rows = ledger.db.execute(
        "SELECT r.*,(SELECT COUNT(*) FROM shared_members m WHERE m.request=r.request) AS job_count FROM shared_requests r WHERE (? IS NULL OR r.request=?) AND r.request>? ORDER BY r.request LIMIT 101",
        (request, request, after or ""),
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
    counts = ledger.db.execute(
        "SELECT COUNT(*),COUNT(DISTINCT m.job_id) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 AND (? IS NULL OR r.request=?)",
        (request, request),
    ).fetchone()
    if request is None:
        unique = ledger.db.execute(
            "SELECT j.id,j.state,j.created FROM shared_jobs s JOIN jobs j ON j.id=s.job_id LEFT JOIN shared_cancelled c ON c.job_id=j.id WHERE c.job_id IS NULL"
        ).fetchall()
    else:
        unique = ledger.db.execute(
            "SELECT DISTINCT j.id,j.state,j.created FROM shared_members m JOIN shared_requests r ON r.request=m.request JOIN jobs j ON j.id=m.job_id WHERE r.active=1 AND r.request=?",
            (request,),
        ).fetchall()
    states = {}
    for row in unique:
        states[row["state"]] = states.get(row["state"], 0) + 1
    oldest = min(
        (row["created"] for row in unique if row["state"] == "queued"),
        default=time.time(),
    )
    maximum = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_max_pending'"
    ).fetchone()[0]
    cancelled = ledger.db.execute(
        "SELECT COUNT(*) FROM shared_cancelled c WHERE (? IS NULL OR EXISTS (SELECT 1 FROM shared_members m WHERE m.job_id=c.job_id AND m.request=?))",
        (request, request),
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
        "unique_jobs": len(unique),
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
