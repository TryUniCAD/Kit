# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import sqlite3
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from Ledger import Ledger
from Records import bounded, canonical, digest, label
from SolidWorksBatchAdmission import (
    AttachBatch,
    HasAttachedBatch,
    IsReserved,
    PrepareAdmission,
    ReleaseAdmission,
    ReserveAdmission,
)
from StoreRead import read_store

sys.path.insert(0, str(Path(__file__).resolve().with_name("ApplicationWorkers")))
from ApplicationProtocol import configuration
from SolidWorksAvailability import (
    BatchPriorityMutex,
    HoldMutex,
    IsSolidWorksRunning,
    OracleMutex,
)

OPERATION = "p01-p03-p04-readback"
SCOPE_CHOICES = ("principal", "cut", "discovery")
LIMIT = 10000


def prepare(ledger):
    PrepareAdmission(ledger.db)
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS solidworks_readback_checks ("
        "installation TEXT NOT NULL, check_id TEXT NOT NULL, scope TEXT NOT NULL, "
        "created REAL NOT NULL, batch_id TEXT REFERENCES jobs(id), definition_hash TEXT, "
        "PRIMARY KEY (installation, check_id))"
    )
    ledger.db.execute(
        "CREATE INDEX IF NOT EXISTS solidworks_readback_pending "
        "ON solidworks_readback_checks (installation, batch_id, check_id)"
    )


def enqueue(ledger, identity, check, scope):
    row = ledger.db.execute(
        "SELECT scope, batch_id FROM solidworks_readback_checks "
        "WHERE installation=? AND check_id=?",
        (identity, check),
    ).fetchone()
    if row is not None:
        if row["scope"] != scope:
            raise ValueError("check ID already identifies another scope")
        return {"check": check, "scope": scope, "batch": row["batch_id"]}
    count = ledger.db.execute(
        "SELECT COUNT(*) FROM solidworks_readback_checks"
    ).fetchone()[0]
    if count >= LIMIT:
        raise ValueError("SOLIDWORKS readback check inventory exceeds its store limit")
    ledger.db.execute(
        "INSERT INTO solidworks_readback_checks (installation, check_id, scope, created) "
        "VALUES (?, ?, ?, ?)",
        (identity, check, scope, time.time()),
    )
    return {"check": check, "scope": scope, "batch": None}


# existing batches get the whole application slot before another cohort is released
def ActiveBatches(Db, Identity):
    return Db.execute(
        "SELECT DISTINCT j.id, j.state FROM solidworks_readback_checks c "
        "JOIN jobs j ON j.id=c.batch_id "
        "WHERE c.installation=? AND j.definition_hash=c.definition_hash "
        "AND j.state IN ('queued','running') ORDER BY j.id",
        (Identity,),
    ).fetchall()


# a production oracle job takes precedence until the backlog crosses both limits
def IsEarlierWorkReady(Db, Resource, Priority):
    return (
        Db.execute(
            "SELECT 1 FROM job_resources r JOIN jobs j ON j.id=r.job_id "
            "WHERE r.resource=? AND (j.state='running' OR "
            "(?=0 AND j.state='queued' AND j.next_run<=?)) LIMIT 1",
            (Resource, Priority, time.time()),
        ).fetchone()
        is not None
    )


# assignment and its controller reservation must be visible in the same transaction
def flush(ledger, identity, installation, wait_seconds=0, oracle_ready=False):
    active = ActiveBatches(ledger.db, identity)
    if active:
        return {"status": "active_batch", "jobs": [dict(row) for row in active]}
    checks = ledger.db.execute(
        "SELECT check_id, scope, created FROM solidworks_readback_checks "
        "WHERE installation=? AND batch_id IS NULL ORDER BY check_id",
        (identity,),
    ).fetchall()
    if not checks:
        return {"status": "empty", "submitted": 0}
    if (
        wait_seconds
        and time.time() - min(check["created"] for check in checks) < wait_seconds
    ):
        return {"status": "collecting", "submitted": 0}
    resource = label("application:" + installation["installation"])
    row = ledger.db.execute(
        "SELECT capacity, available FROM resources WHERE name=?", (resource,)
    ).fetchone()
    if row is None or row["capacity"] != 1:
        raise ValueError(
            "register the SOLIDWORKS application resource with capacity one"
        )
    priority = IsReserved(ledger.db, resource, identity)
    if (
        not row["available"]
        or not oracle_ready
        or IsEarlierWorkReady(ledger.db, resource, priority)
    ):
        return {"status": "waiting_application", "submitted": 0}
    cohort = digest(
        [identity, [[check["check_id"], check["scope"]] for check in checks]]
    )
    job = "readback:solidworks:batch:" + cohort
    if ledger.db.execute("SELECT 1 FROM jobs WHERE id=?", (job,)).fetchone():
        raise ValueError("batch job ID already exists outside the pending roster")
    revision = installation["source_revision"]
    ledger.submit_many(
        [
            {
                "id": job,
                "kind": "capture.solidworks",
                "inputs": {},
                "resources": [resource],
                "options": {
                    "source_revision": revision,
                    "readback_operation": OPERATION,
                },
                "rule_version": "discovery-readback@" + revision,
                "tool_version": "solidworks-worker@" + revision,
                "max_attempts": 1,
                "lease_seconds": 60,
                "timeout_seconds": 300,
            }
        ]
    )
    pin = ledger.db.execute(
        "SELECT definition_hash FROM jobs WHERE id=?", (job,)
    ).fetchone()[0]
    ledger.db.execute(
        "UPDATE solidworks_readback_checks SET batch_id=?, definition_hash=? "
        "WHERE installation=? AND batch_id IS NULL",
        (job, pin, identity),
    )
    if priority:
        AttachBatch(ledger.db, resource, identity, job, pin)
    ledger.event(job, "solidworks_readback_batch_released", {"checks": len(checks)})
    return {
        "status": "submitted",
        "job": job,
        "checks": len(checks),
        "scopes": sorted({row["scope"] for row in checks}),
    }


def status(ledger, identity, after):
    rows = ledger.db.execute(
        "SELECT c.check_id, c.scope, c.batch_id, "
        "CASE WHEN c.batch_id IS NULL THEN 'pending' "
        "WHEN j.definition_hash=c.definition_hash THEN j.state ELSE 'definition_changed' END AS state, "
        "CASE WHEN j.definition_hash=c.definition_hash THEN j.receipt END AS receipt, "
        "CASE WHEN j.definition_hash=c.definition_hash THEN j.result END AS result "
        "FROM solidworks_readback_checks c LEFT JOIN jobs j ON j.id=c.batch_id "
        "WHERE c.installation=? AND c.check_id>? ORDER BY c.check_id LIMIT 101",
        (identity, after),
    ).fetchall()
    return {
        "checks": [dict(row) for row in rows[:100]],
        "next_after": rows[99]["check_id"] if len(rows) > 100 else None,
    }


# oracle probing happens outside the ledger transaction to keep enqueues and claims moving
def TryFlush(Store, Identity, Installation, WaitSeconds=0):
    with HoldMutex(OracleMutex) as OracleFree:
        OracleReady = OracleFree and not IsSolidWorksRunning()
        with Ledger(Store) as State:
            prepare(State)
            return flush(State, Identity, Installation, WaitSeconds, OracleReady)


# the watcher keeps a bounded admission hold while the application drains
def watch(
    store,
    installation,
    identity,
    wait_seconds,
    poll_seconds,
    priority_count,
    priority_age,
):
    resource = label("application:" + installation["installation"])
    database = store.resolve() / "ledger.sqlite3"
    held = False
    with ExitStack() as reservation:
        try:
            while True:
                with read_store(database, None, (4,)) as db:
                    count, oldest = db.execute(
                        "SELECT COUNT(*), MIN(created) FROM solidworks_readback_checks "
                        "WHERE installation=? AND batch_id IS NULL",
                        (identity,),
                    ).fetchone()
                    ready = db.execute(
                        "SELECT 1 FROM resources WHERE name=? AND capacity=1 AND available=1",
                        (resource,),
                    ).fetchone()
                    active = ActiveBatches(db, identity)
                    earlier = IsEarlierWorkReady(db, resource, held)
                    attached = held and HasAttachedBatch(db, resource, identity)
                age = time.time() - oldest if oldest is not None else 0
                due = bool(count and ready and age >= wait_seconds)
                urgent = due and count >= priority_count and age >= priority_age
                if active and held and ready:
                    with Ledger(store) as ledger:
                        ReserveAdmission(
                            ledger.db, resource, identity, 30 + 2 * poll_seconds
                        )
                elif held and (not urgent or attached):
                    with Ledger(store) as ledger:
                        ReleaseAdmission(ledger.db, resource, identity)
                    reservation.close()
                    held = False
                elif urgent and not active and not held:
                    held = reservation.enter_context(HoldMutex(BatchPriorityMutex))
                    if not held:
                        reservation.close()
                if held and not active:
                    with Ledger(store) as ledger:
                        ReserveAdmission(
                            ledger.db, resource, identity, 30 + 2 * poll_seconds
                        )
                        earlier = IsEarlierWorkReady(ledger.db, resource, True)
                if due and not active and not earlier:
                    result = TryFlush(store, identity, installation, wait_seconds)
                    if result["status"] == "submitted":
                        print(canonical(result), flush=True)
                time.sleep(poll_seconds)
        finally:
            if held:
                with Ledger(store) as ledger:
                    ReleaseAdmission(ledger.db, resource, identity)


def main():
    parser = argparse.ArgumentParser(
        description="Collect routine SOLIDWORKS discovery checks for one serial readback"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("enqueue")
    add.add_argument("check")
    add.add_argument("scope", choices=SCOPE_CHOICES)
    commands.add_parser("flush")
    view = commands.add_parser("status")
    view.add_argument("--after")
    watcher = commands.add_parser("watch")
    watcher.add_argument("--wait-seconds", type=int, default=0)
    watcher.add_argument("--poll-seconds", type=int, default=2)
    watcher.add_argument("--priority-count", type=int, default=10)
    watcher.add_argument("--priority-seconds", type=int, default=300)
    args = parser.parse_args()
    try:
        installation = configuration(args.installation)
        if installation["application"] != "solidworks":
            raise ValueError("a SOLIDWORKS installation is required")
        identity = digest(installation)
        if args.command == "watch":
            wait_seconds = bounded(args.wait_seconds, 0, 3600)
            poll_seconds = bounded(args.poll_seconds, 1, 60)
            priority_count = bounded(args.priority_count, 1, LIMIT)
            priority_age = bounded(args.priority_seconds, 0, 86400)
            with Ledger(args.store) as ledger:
                prepare(ledger)
            watch(
                args.store,
                installation,
                identity,
                wait_seconds,
                poll_seconds,
                priority_count,
                priority_age,
            )
            return 0
        if args.command == "flush":
            print(canonical(TryFlush(args.store, identity, installation)))
            return 0
        with Ledger(args.store) as ledger:
            prepare(ledger)
            if args.command == "enqueue":
                result = enqueue(ledger, identity, label(args.check), args.scope)
            else:
                result = status(
                    ledger, identity, label(args.after) if args.after else ""
                )
        print(canonical(result))
        return 0
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"SOLIDWORKS batch error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
