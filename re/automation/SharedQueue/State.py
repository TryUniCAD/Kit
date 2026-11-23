# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from Records import bounded, digest


# existing stores retain their claim behavior until shared coordination is requested
def installed(ledger):
    row = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_version'"
    ).fetchone()
    if row is None:
        return False
    if row[0] != 1:
        raise ValueError("unsupported shared queue extension")
    return True


# one transactional extension preserves the existing durable controller schema
def initialize(ledger):
    if installed(ledger):
        return
    statements = (
        "CREATE TABLE shared_requests (request TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload_hash TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)), priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100), updated REAL NOT NULL)",
        "CREATE TABLE shared_jobs (job_id TEXT PRIMARY KEY REFERENCES jobs(id))",
        "CREATE TABLE shared_members (request TEXT NOT NULL REFERENCES shared_requests(request), local_id TEXT NOT NULL, job_id TEXT NOT NULL REFERENCES shared_jobs(job_id), PRIMARY KEY(request,local_id))",
        "CREATE INDEX shared_subscribers ON shared_members(job_id,request)",
        "CREATE TABLE shared_cancelled (job_id TEXT PRIMARY KEY REFERENCES shared_jobs(job_id))",
    )
    for statement in statements:
        ledger.db.execute(statement)
    ledger.db.executemany(
        "INSERT INTO settings VALUES (?,?)",
        (("shared_queue_version", 1), ("shared_queue_max_pending", 1000)),
    )


# stable identifiers prevent standalone updates from replacing another request's shared definition
def guard_spec(ledger, spec):
    if not spec["id"].startswith("shared:") or not installed(ledger):
        return
    expected = "shared:" + digest(
        {key: value for key, value in spec.items() if key != "id"}
    )
    if spec["id"] != expected:
        raise ValueError(
            "shared job identifiers require their immutable canonical definition"
        )


# backlog admission counts unique unfinished work instead of client aliases
def pending_count(ledger):
    return ledger.db.execute(
        "SELECT COUNT(*) FROM shared_jobs s JOIN jobs j ON j.id=s.job_id LEFT JOIN shared_cancelled c ON c.job_id=j.id WHERE c.job_id IS NULL AND j.state IN ('queued','running','waiting_evidence','waiting_application','waiting_ci')"
    ).fetchone()[0]


# bounded backlog policy is shared by every submitting process
def configure(ledger, maximum):
    maximum = bounded(maximum, 1, 10000)
    initialize(ledger)
    if pending_count(ledger) > maximum:
        raise ValueError("new pending limit is below current shared work")
    ledger.db.execute(
        "UPDATE settings SET value=? WHERE key='shared_queue_max_pending'", (maximum,)
    )
    ledger.event(None, "shared_queue_configured", {"max_pending": maximum})
    return {"queue_version": 1, "max_pending": maximum}
