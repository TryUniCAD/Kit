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

from Ledger import Ledger
from PriorityClaims import runnable_jobs
from PrioritySchedule import initialize as native_schedule
from ProcessClient import Client, job


# independent relational counts check every cached priority including aliases and inactive requests
def check_cache(client):
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        rows = database.execute(
            "SELECT d.job_id,d.priority,d.rank,j.created,COALESCE((SELECT MAX(r.priority) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE m.job_id=d.job_id AND r.active=1),50),d.pool,(SELECT pool FROM pool_kinds WHERE kind=j.kind),d.state,j.state FROM shared_dispatch d JOIN jobs j ON j.id=d.job_id"
        ).fetchall()
        for (
            identity,
            priority,
            rank,
            created,
            expected,
            pool,
            actual_pool,
            state,
            actual_state,
        ) in rows:
            assert (priority, rank, pool, state) == (
                expected,
                expected * 60 - created,
                actual_pool,
                actual_state,
            ), identity
        assert database.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == len(rows)
        actual = database.execute(
            "SELECT m.job_id,r.priority,COUNT(*) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 GROUP BY m.job_id,r.priority ORDER BY 1,2"
        ).fetchall()
        cached = database.execute(
            "SELECT job_id,priority,refs FROM shared_rank_votes WHERE refs>0 ORDER BY 1,2"
        ).fetchall()
        assert actual == cached


# process mutations must preserve zero priority and duplicate subscriptions through cancellation and retries
def transitions(root):
    client = Client(root / "Transitions")
    identity = client.enqueue("low", [job("one"), job("duplicate")], priority=0)[
        "jobs"
    ]["one"]
    client.enqueue("high", [job("alias")], priority=100)
    check_cache(client)
    client.run("cancel-request", "high", "--revision", "1")
    check_cache(client)
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        assert (
            database.execute(
                "SELECT priority FROM shared_dispatch WHERE job_id=?", (identity,)
            ).fetchone()[0]
            == 0
        )
    client.enqueue("low", [job("one")], revision=1, priority=12)
    client.enqueue("high", [job("alias")], revision=2, priority=70)
    client.enqueue("high", [job("alias")], revision=3, priority=9)
    check_cache(client)
    client.run("cancel-request", "low", "--revision", "2")
    client.run("cancel-request", "high", "--revision", "4")
    check_cache(client)
    client.enqueue("low", [job("restored")], revision=3, priority=0)
    client.run("pool", "decode", "--kind", "fixture.decode")
    check_cache(client)
    client.run("pool", "decode", "--kind", "fixture.other")
    check_cache(client)
    with Ledger(client.root / "State") as ledger:
        ledger.submit_many([job("standalone", kind="fixture.other")])
        before = [
            tuple(row)
            for row in ledger.db.execute(
                "SELECT * FROM shared_dispatch ORDER BY job_id"
            )
        ]
    try:
        with Ledger(client.root / "State") as ledger:
            ledger.db.execute("UPDATE shared_requests SET priority=99,active=1")
            ledger.db.execute("UPDATE jobs SET created=created-900")
            raise RuntimeError("fixture rollback")
    except RuntimeError:
        pass
    with Ledger(client.root / "State") as ledger:
        assert before == [
            tuple(row)
            for row in ledger.db.execute(
                "SELECT * FROM shared_dispatch ORDER BY job_id"
            )
        ]
        triggers = ledger.db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND (name LIKE 'shared_dispatch_%' OR name LIKE 'shared_rank_%')"
        ).fetchall()
        for row in triggers:
            ledger.db.execute('DROP TRIGGER "' + row[0] + '"')
        ledger.db.execute("DROP TABLE shared_dispatch")
        ledger.db.execute("DROP TABLE shared_rank_votes")
        ledger.db.execute(
            "DELETE FROM settings WHERE key='shared_queue_dispatch_version'"
        )
    claimed, lease = client.claim("Migrated")
    assert claimed == "standalone"
    client.finish(lease)
    claimed, lease = client.claim("MigratedShared")
    assert claimed == identity
    client.finish(lease)
    check_cache(client)
    with Ledger(client.root / "State") as ledger:
        ledger.db.execute(
            "UPDATE settings SET value=2 WHERE key='shared_queue_dispatch_version'"
        )
    assert "unsupported shared queue dispatch" in client.run(
        "claim",
        "--worker",
        "invalid",
        "--claim-file",
        client.root / "Invalid.json",
        code=1,
    )
    return {
        "migration_verified": True,
        "rollback_verified": True,
        "subscription_priority_verified": True,
    }


# measure only candidate selection because artifact verification and lease writes have separate existing costs
def select_steps(ledger, pool, count=1):
    steps, statements = [0], []
    ledger.db.set_progress_handler(lambda: steps.__setitem__(0, steps[0] + 1) or 0, 1)
    ledger.db.set_trace_callback(statements.append)
    try:
        cursor = runnable_jobs(ledger, pool, grouped=count > 1)
        try:
            rows = cursor.fetchmany(count)
        finally:
            cursor.close()
    finally:
        ledger.db.set_progress_handler(None, 0)
        ledger.db.set_trace_callback(None)
    sql = next(
        value
        for value in reversed(statements)
        if value.lstrip().startswith("SELECT j.*")
    )
    plan = [row[3] for row in ledger.db.execute("EXPLAIN QUERY PLAN " + sql)]
    assert not any("TEMP B-TREE" in item for item in plan), plan
    assert any("shared_dispatch_" in item for item in plan), plan
    return rows, steps[0]


# indexed draining must stay linear overall and seek a multi-kind pool past unrelated native backlog
def scale(root):
    client = Client(root / "Scale")
    client.run("queue-config", "--max-pending", "10000")
    client.run("pool", "offline", "--kind", "fixture.decode", "--kind", "fixture.extra")
    client.run("pool", "native", "--kind", "fixture.native")
    client.run("resource", "native:installation", "--capacity", "1", "--unavailable")
    with Ledger(client.root / "State") as ledger:
        small = [
            job(
                f"ready:{index:04d}",
                kind="fixture.decode" if index % 2 else "fixture.extra",
                options={"case": index},
            )
            for index in range(8)
        ]
        ledger.submit_many(small)
        _, small_global = select_steps(ledger, None)
        _, small_pool = select_steps(ledger, "offline", 2)
        ledger.submit_many(
            [
                job(
                    f"ready:{index:04d}",
                    kind="fixture.decode" if index % 2 else "fixture.extra",
                    options={"case": index},
                )
                for index in range(8, 2000)
            ]
        )
        ledger.submit_many(
            [
                job(
                    f"native:{index:04d}",
                    kind="fixture.native",
                    resources=["native:installation"],
                    options={"case": index},
                )
                for index in range(2000)
            ]
        )
        ledger.db.execute(
            "UPDATE jobs SET state='queued',created=created-10000 WHERE kind='fixture.native'"
        )
        _, large_pool = select_steps(ledger, "offline", 2)
        ledger.db.execute(
            "UPDATE jobs SET state='waiting_application' WHERE kind='fixture.native'"
        )
        _, large_global = select_steps(ledger, None)
        assert large_pool <= small_pool + 100 and large_global <= small_global + 100, (
            small_global,
            large_global,
            small_pool,
            large_pool,
        )
        expected = [
            row[0]
            for row in ledger.db.execute(
                "SELECT job_id FROM shared_dispatch WHERE state='queued' AND pool='offline' ORDER BY rank DESC,created,job_id"
            )
        ]
        total = 0
        for identity in expected:
            rows, steps = select_steps(ledger, "offline")
            assert len(rows) == 1 and rows[0]["id"] == identity
            assert steps <= 500, steps
            total += steps
            ledger.db.execute("UPDATE jobs SET state='failed' WHERE id=?", (identity,))
        assert not select_steps(ledger, "offline")[0]
        assert total < len(expected) * 500
    check_cache(client)
    return {
        "drained_jobs": len(expected),
        "drain_selection_steps": total,
        "small_global_steps": small_global,
        "large_global_steps": large_global,
        "small_pool_group_steps": small_pool,
        "large_pool_group_steps": large_pool,
        "unrelated_native_backlog": 2000,
    }


# native lane and requested-work reservations retain precedence over cached shared urgency
def native(root):
    client = Client(root / "Native")
    low = client.enqueue(
        "requested", [job("requested", options={"case": "requested"})], priority=0
    )["jobs"]["requested"]
    high = client.enqueue(
        "standard", [job("standard", options={"case": "standard"})], priority=100
    )["jobs"]["standard"]
    client.run("resource", "native:installation", "--capacity", "1", "--available")
    with Ledger(client.root / "State") as ledger:
        native_schedule(ledger)
        for identity, lane in ((low, 0), (high, 2)):
            definition = ledger.db.execute(
                "SELECT definition_hash FROM jobs WHERE id=?", (identity,)
            ).fetchone()[0]
            ledger.db.execute(
                "INSERT INTO a07_priority VALUES (?,?,?,?,?,?,?)",
                (
                    identity,
                    lane,
                    "fixture",
                    "[]",
                    "[]",
                    "native:installation",
                    definition,
                ),
            )
        for grouped in (False, True):
            cursor = runnable_jobs(ledger, None, grouped=grouped)
            rows = cursor.fetchall()
            assert [row["id"] for row in rows] == [low]
        ledger.db.execute(
            "UPDATE jobs SET next_run=? WHERE id=?", (time.time() + 1000, low)
        )
        assert runnable_jobs(ledger, None).fetchone()["id"] == high
    return {"native_reservation_verified": True}


# solo and grouped leases share continuous aging while unavailable resources and delayed retries remain excluded
def fairness(root):
    client = Client(root / "Fairness")
    source = client.root / "Input.bin"
    source.write_bytes(b"real group evidence")
    client.run("bind", "evidence:ranking", source)
    client.run("pool", "decode", "--kind", "fixture.decode")
    client.run("resource", "blocked:installation", "--capacity", "1", "--unavailable")

    def shared(request, priority, **settings):
        return client.enqueue(
            request,
            [
                job(
                    "alias",
                    inputs={"source": "evidence:ranking"},
                    options={"case": request},
                    **settings,
                )
            ],
            priority=priority,
        )["jobs"]["alias"]

    old = shared("old", 0)
    urgent = shared("urgent", 100)
    low = shared("low", 0)
    blocked = shared("blocked", 100, resources=["blocked:installation"])
    delayed = shared("delayed", 100)
    with Ledger(client.root / "State") as ledger:
        ledger.db.execute("UPDATE jobs SET created=created-121*60 WHERE id=?", (old,))
        ledger.db.execute(
            "UPDATE jobs SET state='queued',created=created-100000 WHERE id=?",
            (blocked,),
        )
        ledger.db.execute(
            "UPDATE jobs SET next_run=?,created=created-100000 WHERE id=?",
            (time.time() + 1000, delayed),
        )
        assert runnable_jobs(ledger, "decode").fetchone()["id"] == old
    registry = client.write(
        {
            "group_registry_version": 1,
            "kinds": {"fixture.decode": {"limit_bytes": 1048576, "max_members": 2}},
        }
    )
    directory = client.root / "Group"
    result = client.run(
        "claim-group",
        "--worker",
        "worker:ranked",
        "--pool",
        "decode",
        "--registry",
        registry,
        "--claim-dir",
        directory,
    )
    assert result["count"] == 2
    identities = [
        json.loads((directory / f"{index:02d}.json").read_text())["job"]["id"]
        for index in range(2)
    ]
    assert identities == [old, urgent], identities
    assert client.claim("LowNext", "decode")[0] == low
    assert client.claim("OnlyBlockedAndDelayed", "decode")[0] is None
    check_cache(client)
    return {"solo_group_fairness_verified": True}


# real controller processes and sqlite progress counters establish dispatch correctness and bounded work
def main():
    with tempfile.TemporaryDirectory(prefix="kit-queue-dispatch-") as temporary:
        root = Path(temporary)
        result = {**transitions(root), **scale(root), **native(root), **fairness(root)}
    print(json.dumps({"status": "passed", **result}))


if __name__ == "__main__":
    main()
