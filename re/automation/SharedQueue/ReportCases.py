# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import sqlite3
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Artifacts import Artifacts
from Ledger import Ledger
from ProcessClient import Client, job
from Records import canonical, digest, specification
from SharedQueue.Plan import request_plan
from SharedQueue.Report import queue_status


# actual relational state supplies an independent oracle for the maintained reporting read model
def check_report(client, request=None, after=None):
    arguments = ("--request", request) if request is not None else ()
    arguments += ("--after", after) if after is not None else ()
    before = time.time()
    report = client.run("queue-status", *arguments)
    finished = time.time()
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        database.row_factory = sqlite3.Row
        rows = database.execute(
            "SELECT * FROM shared_requests WHERE (? IS NULL OR request=?) AND request>? ORDER BY request LIMIT 101",
            (request, request, after or ""),
        ).fetchall()
        summaries = []
        for row in rows[:100]:
            members = dict(
                database.execute(
                    "SELECT local_id,job_id FROM shared_members WHERE request=? ORDER BY local_id",
                    (row["request"],),
                )
            )
            summary = {
                "request": row["request"],
                "revision": row["revision"],
                "active": bool(row["active"]),
                "priority": row["priority"],
                "job_count": len(members),
            }
            if request is not None:
                summary["jobs"] = members
            summaries.append(summary)
        counts = database.execute(
            "SELECT COUNT(*),COUNT(DISTINCT m.job_id) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 AND (? IS NULL OR r.request=?)",
            (request, request),
        ).fetchone()
        if request is None:
            unique = database.execute(
                "SELECT j.id,j.state,j.created FROM shared_jobs s JOIN jobs j ON j.id=s.job_id LEFT JOIN shared_cancelled c ON c.job_id=j.id WHERE c.job_id IS NULL"
            ).fetchall()
        else:
            unique = database.execute(
                "SELECT DISTINCT j.id,j.state,j.created FROM shared_members m JOIN shared_requests r ON r.request=m.request JOIN jobs j ON j.id=m.job_id WHERE r.active=1 AND r.request=?",
                (request,),
            ).fetchall()
        states = {}
        for row in unique:
            states[row["state"]] = states.get(row["state"], 0) + 1
        cancelled = database.execute(
            "SELECT COUNT(*) FROM shared_cancelled c WHERE (? IS NULL OR EXISTS(SELECT 1 FROM shared_members m WHERE m.job_id=c.job_id AND m.request=?))",
            (request, request),
        ).fetchone()[0]
        expected = {
            "requests": summaries,
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
        }
        for key, value in expected.items():
            if report[key] != value:
                raise AssertionError(
                    f"report field {key} differs: {report[key]} != {value}"
                )
        queued = [row["created"] for row in unique if row["state"] == "queued"]
        if queued:
            oldest = min(queued)
            if (
                not max(0, before - oldest)
                <= report["oldest_queued_seconds"]
                <= max(0, finished - oldest)
            ):
                raise AssertionError(
                    "oldest queue index does not match the actual job creation time"
                )
        elif report["oldest_queued_seconds"] > finished - before + 0.001:
            raise AssertionError("empty queued scope reports a stale oldest item")
    if (
        report["scope"] != "queue_metadata"
        or report["acceptance_verified"] is not False
        or report["artifact_bytes_hashed"] != 0
    ):
        raise AssertionError(
            "metadata poll changed its evidence or acceptance contract"
        )
    return report


# process mutations must preserve exact counts for aliases toggles cancellation invalidation and rollback
def transitions(root):
    client = Client(root / "Transitions")
    first = job("first")
    alias = job("alias")
    shared = client.enqueue("first", [first, alias])["jobs"]["first"]
    client.enqueue("second", [job("second")])
    for request in (None, "first", "second", "unknown"):
        check_report(client, request)
    check_report(client, "first", "zz")
    claimed, lease = client.claim("ReportComplete")
    if claimed != shared:
        raise AssertionError("real shared completion selected another job")
    client.finish(lease)
    check_report(client)
    client.run("cancel-request", "first", "--revision", "1")
    check_report(client, "first")
    check_report(client)
    client.run("cancel-request", "second", "--revision", "1")
    check_report(client)
    client.run("cancel-request", "second", "--revision", "1")
    check_report(client)
    client.enqueue("first", [first, job("new", options={"case": "new"})], revision=2)
    check_report(client)
    client.enqueue(
        "first", [job("replacement", options={"case": "replacement"})], revision=3
    )
    check_report(client)
    source = client.root / "Input.bin"
    source.write_bytes(b"original")
    client.run("bind", "evidence:report", source)
    identity = client.enqueue(
        "input", [job("input", inputs={"source": "evidence:report"})], priority=100
    )["jobs"]["input"]
    claimed, lease = client.claim("ReportInput")
    if claimed != identity:
        raise AssertionError("input report fixture did not acquire the real claim")
    client.finish(lease)
    check_report(client)
    source.write_bytes(b"changed")
    client.run("bind", "evidence:report", source)
    check_report(client)
    client.run("cancel-request", "input", "--revision", "1")
    source.write_bytes(b"later")
    client.run("bind", "evidence:report", source)
    check_report(client)
    client.enqueue(
        "input", [job("renamed", inputs={"source": "evidence:report"})], revision=2
    )
    check_report(client)
    before = check_report(client)
    client.run("queue-config", "--max-pending", str(before["pending_jobs"]))
    client.enqueue("overflow", [job("overflow", options={"case": "overflow"})], code=1)
    after = check_report(client)
    for key in (
        "subscriptions",
        "unique_jobs",
        "pending_jobs",
        "states",
        "cancelled_jobs",
    ):
        if before[key] != after[key]:
            raise AssertionError("rollback changed the maintained report read model")
    return {"state_transitions": True, "rollback_verified": True}


# sqlite virtual machine steps directly expose retained history scans while holding the controller transaction
def profile(client, request=None):
    steps = [0]

    def progress():
        steps[0] += 1
        return int(steps[0] > 100000)

    with Ledger(client.root / "State") as ledger:
        ledger.db.set_progress_handler(progress, 1)
        try:
            queue_status(ledger, request)
        finally:
            ledger.db.set_progress_handler(None, 0)
    return steps[0]


# retained metadata can approach both documented quotas without implying successful CAD work
def grow_history(client, target):
    store = client.root / "State"
    objects = Artifacts(store)
    with closing(sqlite3.connect(store / "ledger.sqlite3")) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        size = 0
        for index in range(7999):
            spec = specification(
                job(
                    "history",
                    inputs={"source": "missing:history"},
                    options={"case": index},
                )
            )
            spec["id"] = "shared:" + digest(
                {key: value for key, value in spec.items() if key != "id"}
            )
            encoded = canonical(spec)
            source_hash = objects.put_record(spec)
            size += len(encoded.encode("utf-8"))
            database.execute(
                "INSERT INTO jobs(id,kind,definition,definition_hash,state,generation,fingerprint,snapshot,parked,reason,created) VALUES (?,?,?,?,'rejected',1,NULL,NULL,1,'shared request superseded',?)",
                (spec["id"], spec["kind"], encoded, source_hash, time.time() - index),
            )
            database.execute("INSERT INTO shared_jobs VALUES (?)", (spec["id"],))
            database.execute("INSERT INTO shared_cancelled VALUES (?)", (spec["id"],))
        database.execute("UPDATE settings SET value=value+7999 WHERE key='job_count'")
        database.execute(
            "UPDATE settings SET value=value+? WHERE key='definition_bytes'", (size,)
        )
        for index in range(99):
            request = f"noise:{index:03d}"
            count = 999 if index == 98 else 1000
            for member in range(1, count):
                database.execute(
                    "INSERT INTO shared_members VALUES (?,?,?)",
                    (request, f"alias:{member:04d}", target),
                )
            plan = request_plan(
                {
                    "queue_version": 1,
                    "request": request,
                    "revision": 0,
                    "jobs": [job("only")]
                    + [job(f"alias:{member:04d}") for member in range(1, count)],
                }
            )
            database.execute(
                "UPDATE shared_requests SET payload_hash=? WHERE request=?",
                (digest(plan), request),
            )
        database.commit()


# legacy shared stores receive one atomic backfill and subsequent polls use only the maintained model
def migrate_report(client):
    path = client.root / "State/ledger.sqlite3"
    with closing(sqlite3.connect(path)) as database:
        names = [
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'shared_report_%'"
            )
        ]
        for name in names:
            database.execute('DROP TRIGGER "' + name.replace('"', '""') + '"')
        for name in (
            "shared_report_items",
            "shared_report_requests",
            "shared_report_states",
            "shared_report_totals",
        ):
            database.execute("DROP TABLE " + name)
        database.execute("DELETE FROM settings WHERE key='shared_queue_report_version'")
        database.commit()
    check_report(client)
    with closing(sqlite3.connect(path)) as database:
        database.execute(
            "UPDATE settings SET value=2 WHERE key='shared_queue_report_version'"
        )
        database.commit()
    error = client.run("queue-status", code=1)
    if "unsupported shared queue report extension" not in error:
        raise AssertionError("future reporting schema did not fail closed")
    with closing(sqlite3.connect(path)) as database:
        database.execute(
            "UPDATE settings SET value=1 WHERE key='shared_queue_report_version'"
        )
        database.commit()


# global polling and exact request polling must be independent of unrelated retained history
def scale(root):
    client = Client(root / "Scale")
    target = client.enqueue(
        "target", [job(f"target:{index:04d}") for index in range(1000)]
    )["jobs"]["target:0000"]
    for index in range(99):
        client.enqueue(f"noise:{index:03d}", [job("only")])
    client.enqueue("zz:last", [job("tail")])
    client.run("cancel-request", "zz:last", "--revision", "1")
    check_report(client)
    small_global, small_request = profile(client), profile(client, "target")
    grow_history(client, target)
    global_report = check_report(client)
    check_report(client, None, global_report["next_after"])
    check_report(client, "target")
    check_report(client, "zz:last")
    check_report(client, "noise:098", "zz")
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        jobs, members = database.execute(
            "SELECT (SELECT COUNT(*) FROM shared_jobs),(SELECT COUNT(*) FROM shared_members)"
        ).fetchone()
        database.execute("UPDATE jobs SET created=created-1000 WHERE id=?", (target,))
        database.commit()
    if jobs != 8000 or members != 100000:
        raise AssertionError(f"scale fixture missed its quotas: {jobs}/{members}")
    check_report(client)
    large_global, large_request = profile(client), profile(client, "target")
    if large_global > small_global + 2000 or large_request > small_request + 2000:
        raise AssertionError(
            f"polling cost depends on unrelated history: {small_global}/{large_global} {small_request}/{large_request}"
        )
    migrate_report(client)
    migrated_global, migrated_request = profile(client), profile(client, "target")
    if migrated_global > large_global + 2000 or migrated_request > large_request + 2000:
        raise AssertionError("migrated polling rescans retained history")
    return {
        "retained_jobs": jobs,
        "retained_subscriptions": members,
        "small_global_steps": small_global,
        "large_global_steps": large_global,
        "small_request_steps": small_request,
        "large_request_steps": large_request,
        "migration_verified": True,
    }


# the actual controller and sqlite read model jointly establish reporting correctness and bounded work
def main():
    with tempfile.TemporaryDirectory(prefix="kit-queue-report-") as temporary:
        root = Path(temporary)
        changed = transitions(root)
        measured = scale(root)
    print(
        json.dumps({"status": "passed", "scenario": "reporting", **changed, **measured})
    )


if __name__ == "__main__":
    main()
