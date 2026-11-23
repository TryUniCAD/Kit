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
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Ledger import Ledger
from ProcessClient import Client, job
from SharedQueue.Lifecycle import reconcile_members
from SharedQueue.Submit import enqueue, cancel


# raw dependency edges independently prove that maintained demand counts include every live child state
def check_demand(client):
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        actual = dict(
            database.execute(
                "SELECT d.dependency,COUNT(*) FROM dependencies d LEFT JOIN shared_cancelled c ON c.job_id=d.job_id WHERE c.job_id IS NULL GROUP BY d.dependency"
            )
        )
        cached = dict(
            database.execute(
                "SELECT dependency,live_children FROM shared_demand WHERE live_children>0"
            )
        )
        assert cached == actual, (cached, actual)
        assert (
            database.execute(
                "SELECT COUNT(*) FROM shared_demand WHERE live_children<0"
            ).fetchone()[0]
            == 0
        )
        return dict(
            database.execute("SELECT dependency,live_children FROM shared_demand")
        )


# distinct subscribed children reproduce the common prerequisite fanout seen in parallel research campaigns
def child_record(index, parent):
    return {
        "queue_version": 1,
        "request": f"child:{index:04d}",
        "revision": 0,
        "jobs": [job("child", depends_on=[parent], options={"case": index})],
    }


# actual admission includes mutation triggers and reconciliation rather than timing an isolated counter read
def profile(ledger, index, parent):
    steps = [0]
    previous = getattr(ledger, "shared_reconciled", 0)
    ledger.db.set_progress_handler(lambda: steps.__setitem__(0, steps[0] + 1) or 0, 1)
    try:
        result = enqueue(ledger, child_record(index, parent))
    finally:
        ledger.db.set_progress_handler(None, 0)
    assert result["shared_reconciled_jobs"] - previous == 2
    return steps[0]


# fanout affects genuine propagation only when state changes and never every independent admission
def fanout(root):
    client = Client(root / "Fanout")
    client.run("queue-config", "--max-pending", "10000")
    parent = client.enqueue("root", [job("root")])["jobs"]["root"]
    claimed, lease = client.claim("Root")
    assert claimed == parent
    client.finish(lease)
    receipt = client.state(parent)["receipt"]
    client.run("cancel-request", "root", "--revision", "1")
    first = child_record(0, parent)
    client.run("enqueue", client.write(first))
    with Ledger(client.root / "State") as ledger:
        small = profile(ledger, 1, parent)
        for index in range(2, 2000):
            enqueue(ledger, child_record(index, parent))
        large = profile(ledger, 2000, parent)
        assert large <= small + 1000, (small, large)
        assert (
            ledger.db.execute(
                "SELECT active_refs FROM shared_report_items WHERE job_id=?", (parent,)
            ).fetchone()[0]
            == 0
        )
        assert (
            ledger.db.execute(
                "SELECT live_children FROM shared_demand WHERE dependency=?", (parent,)
            ).fetchone()[0]
            == 2001
        )
    check_demand(client)
    with Ledger(client.root / "State") as ledger:
        for index in range(2000):
            cancel(ledger, f"child:{index:04d}", 1)
        assert (
            ledger.db.execute(
                "SELECT 1 FROM shared_cancelled WHERE job_id=?", (parent,)
            ).fetchone()
            is None
        )
    client.run("cancel-request", "child:2000", "--revision", "1")
    assert client.state(parent)["state"] == "completed"
    assert client.state(parent)["receipt"] == receipt
    check_demand(client)
    with closing(sqlite3.connect(client.root / "State/ledger.sqlite3")) as database:
        assert (
            database.execute(
                "SELECT 1 FROM shared_cancelled WHERE job_id=?", (parent,)
            ).fetchone()
            is not None
        )
        assert (
            database.execute(
                "SELECT live_children FROM shared_demand WHERE dependency=?", (parent,)
            ).fetchone()[0]
            == 0
        )
    client.run("submit", client.write(job("ordinary", depends_on=[parent])))
    assert client.state(parent)["receipt"] == receipt
    with Ledger(client.root / "State") as ledger:
        assert (
            ledger.db.execute(
                "SELECT 1 FROM shared_cancelled WHERE job_id=?", (parent,)
            ).fetchone()
            is None
        )
        for state in ("failed", "rejected", "completed"):
            ledger.db.execute("UPDATE jobs SET state=? WHERE id='ordinary'", (state,))
            reconcile_members(ledger, {parent})
            assert (
                ledger.db.execute(
                    "SELECT 1 FROM shared_cancelled WHERE job_id=?", (parent,)
                ).fetchone()
                is None
            )
    client.run("submit", client.write(job("ordinary", depends_on=["future:parent"])))
    check_demand(client)
    with Ledger(client.root / "State") as ledger:
        assert (
            ledger.db.execute(
                "SELECT live_children FROM shared_demand WHERE dependency='future:parent'"
            ).fetchone()[0]
            == 1
        )
        ledger.db.execute(
            "UPDATE dependencies SET dependency=? WHERE job_id='ordinary'", (parent,)
        )
        reconcile_members(ledger, {parent, "future:parent"})
    check_demand(client)
    client.run("submit", client.write(job("ordinary")))
    check_demand(client)
    return (
        client,
        parent,
        {
            "fanout_children": 2001,
            "small_admission_steps": small,
            "large_admission_steps": large,
            "completed_cache_preserved": True,
            "standalone_child_states_verified": True,
        },
    )


# extension bootstrap and refused transactions must leave the same durable edge accounting as ordinary submissions
def boundaries(client, parent):
    before = check_demand(client)
    try:
        with Ledger(client.root / "State") as ledger:
            ledger.submit_many(
                [
                    job("cycle:a", depends_on=["cycle:b", parent]),
                    job("cycle:b", depends_on=["cycle:a"]),
                ]
            )
    except ValueError as error:
        assert "cycle" in str(error)
    else:
        raise AssertionError("cyclic submission unexpectedly admitted")
    assert check_demand(client) == before
    client.run("queue-config", "--max-pending", "1")
    client.enqueue("occupant", [job("occupant", options={"case": "occupant"})])
    before = check_demand(client)
    record = child_record(2001, parent)
    refused = client.run("enqueue", client.write(record), code=1)
    assert "pending" in refused
    assert check_demand(client) == before
    with Ledger(client.root / "State") as ledger:
        triggers = ledger.db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'shared_demand_%'"
        ).fetchall()
        for row in triggers:
            ledger.db.execute('DROP TRIGGER "' + row[0] + '"')
        ledger.db.execute("DROP TABLE shared_demand")
        ledger.db.execute(
            "DELETE FROM settings WHERE key='shared_queue_demand_version'"
        )
    client.run("submit", client.write(job("legacy:ordinary", depends_on=[parent])))
    check_demand(client)
    assert client.state(parent)["state"] == "completed"
    with Ledger(client.root / "State") as ledger:
        ledger.db.execute(
            "UPDATE settings SET value=2 WHERE key='shared_queue_demand_version'"
        )
    unsupported = client.run("submit", client.write(job("invalid")), code=1)
    assert "unsupported shared queue demand" in unsupported
    return {
        "migration_verified": True,
        "rollback_verified": True,
        "forward_reference_verified": True,
    }


# real controller processes and sqlite instruction counters verify fanout-independent demand reconciliation
def main():
    with tempfile.TemporaryDirectory(prefix="kit-queue-demand-") as temporary:
        client, parent, measured = fanout(Path(temporary))
        changed = boundaries(client, parent)
    print(json.dumps({"status": "passed", **measured, **changed}))


if __name__ == "__main__":
    main()
